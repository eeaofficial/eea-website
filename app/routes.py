from app import app
from flask import render_template, request, redirect, url_for, session, flash
from app.utils import load_data, save_data
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "app/static/uploads/members"




@app.route("/")
def home():
    data = load_data()
    return render_template(
        "home.html",
        eea=data["eea_description"],
        upcoming=data["upcoming_event"]
    )

@app.context_processor
def inject_global_data():
    data = load_data()
    return {
        "contact": data["contact"],
        "eea_title": data["eea_description"]["title"]
    }


@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# ---------------- PUBLIC PAGES ----------------


@app.route("/activities")
def activities():
    return render_template("activities.html")


@app.route("/members")
def members():
    data = load_data()
    return render_template(
        "members.html",
        members=data["members"]
    )


@app.route("/gallery")
def gallery():
    data = load_data()
    return render_template(
        "gallery.html",
        galleries=data["gallery"]
    )


@app.route("/upcoming-events")
def upcoming_events():
    with open(EEA_JSON_PATH, "r") as f:
        eea = json.load(f)

    return render_template(
        "upcoming_events.html",
        upcoming_event=eea["upcoming_event"]
    )


# ---------------- MASTER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        data = load_data()
        security = data["security"]

        if (
            email == security["master_email"]
            and password == security["master_password"]
        ):
            session.clear()
            session["master_authenticated"] = True
            session["role"] = "super"
            return redirect(url_for("access_level"))

        flash("Invalid email or master password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")



# ---------------- ACCESS LEVEL ----------------

@app.route("/access-level")
def access_level():

    if not session.get("master_authenticated"):
        return redirect(url_for("login"))

    data = load_data()
    roles = data["security"]["role_passwords"].keys()

    return render_template(
        "access_level.html",
        roles=roles
    )

# ---------------- ROLE PASSWORD ----------------

@app.route("/role-login/<role>", methods=["GET", "POST"])
def role_login(role):

    if not session.get("master_authenticated"):
        return redirect(url_for("login"))

    data = load_data()
    security = data["security"]

    if role not in security["role_passwords"]:
        return redirect(url_for("access_level"))

    if request.method == "POST":
        entered_password = request.form.get("role_password")

        if entered_password == security["role_passwords"][role]:
            session["role"] = role
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect role password", "error")
        return redirect(url_for("role_login", role=role))

    return render_template(
        "role_login.html",
        role_name=role.capitalize() + " Admin"
    )



# ---------------- DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():
    role = session.get("role")

    if not role:
        return redirect(url_for("login"))

    return render_template("dashboard.html", role=role)

import json
import os

EEA_JSON_PATH = os.path.join("app", "data", "eea.json")


@app.route("/admin/upcoming-event", methods=["GET", "POST"])
def manage_upcoming_event():

    role = session.get("role")
    if role not in ["super", "event"]:
        return redirect(url_for("login"))

    with open(EEA_JSON_PATH, "r") as f:
        eea = json.load(f)

    if request.method == "POST":
        eea["upcoming_event"]["active"] = True if request.form.get("active") == "on" else False
        eea["upcoming_event"]["title"] = request.form.get("title")
        eea["upcoming_event"]["date"] = request.form.get("date")
        eea["upcoming_event"]["description"] = request.form.get("description")

        with open(EEA_JSON_PATH, "w") as f:
            json.dump(eea, f, indent=4)

        flash("Upcoming event updated successfully", "success")
        return redirect(url_for("manage_upcoming_event"))

    return render_template(
        "admin_upcoming_event.html",
        event=eea["upcoming_event"]
    )


@app.route("/admin/eea-description", methods=["GET", "POST"])
def edit_eea_description():

    # Allow ONLY Super Admin
    if session.get("role") != "super":
        return redirect(url_for("admin_dashboard"))

    data = load_data()

    if request.method == "POST":
        data["eea_description"]["title"] = request.form.get("title")
        data["eea_description"]["content"] = request.form.get("content")

        save_data(data)
        flash("EEA description updated successfully", "success")

        return redirect(url_for("admin_dashboard"))

    return render_template(
        "edit_eea.html",
        eea=data["eea_description"]
    )

@app.route("/admin/contact-footer", methods=["GET", "POST"])
def edit_contact_footer():

    if session.get("role") != "super":
        return redirect(url_for("admin_dashboard"))

    data = load_data()

    if request.method == "POST":
        data["contact"]["email"] = request.form.get("email")
        data["contact"]["instagram"] = request.form.get("instagram")
        data["contact"]["linkedin"] = request.form.get("linkedin")
        data["contact"]["footer_note"] = request.form.get("footer_note")

        save_data(data)
        flash("Contact & footer updated successfully", "success")

        return redirect(url_for("admin_dashboard"))

    return render_template(
        "edit_contact.html",
        contact=data["contact"]
    )

@app.route("/admin/switch/<role>")
def switch_role(role):

    # Only Super Admin can switch roles
    if session.get("role") != "super":
        return redirect(url_for("login"))

    if role not in ["content", "event"]:
        return redirect(url_for("admin_dashboard"))

    session["role"] = role
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/security", methods=["GET", "POST"])
def security_settings():

    if session.get("role") != "super":
        return redirect(url_for("login"))

    data = load_data()   # your JSON loader
    security = data["security"]

    if request.method == "POST":

        security["master_email"] = request.form["master_email"]

        if request.form["master_password"]:
            security["master_password"] = request.form["master_password"]

        if request.form["super_password"]:
            security["role_passwords"]["super"] = request.form["super_password"]

        if request.form["content_password"]:
            security["role_passwords"]["content"] = request.form["content_password"]

        if request.form["event_password"]:
            security["role_passwords"]["event"] = request.form["event_password"]

        save_data(data)
        flash("Security settings updated successfully", "success")

        return redirect(url_for("security_settings"))

    return render_template(
        "admin/security.html",
        security=security
    )


@app.route("/admin/members")
def manage_members():

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()
    return render_template(
        "admin/manage_members.html",
        members=data["members"]
    )

from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "members")

@app.route("/admin/members/edit/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()
    member = next((m for m in data["members"] if m["id"] == member_id), None)

    if not member:
        flash("Member not found", "error")
        return redirect(url_for("manage_members"))

    if request.method == "POST":
        member["name"] = request.form["name"]
        member["role"] = request.form["role"]
        member["type"] = request.form["type"]

        # ---------- REMOVE PHOTO ----------
        remove_photo = request.form.get("remove_photo")
        if remove_photo and member.get("photo"):
            photo_path = os.path.join(UPLOAD_FOLDER, member["photo"])
            if os.path.exists(photo_path):
                os.remove(photo_path)
            member["photo"] = ""

        # ---------- UPLOAD NEW PHOTO ----------
        photo = request.files.get("photo")
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            photo.save(os.path.join(UPLOAD_FOLDER, filename))
            member["photo"] = filename

        save_data(data)
        flash("Member updated successfully", "success")
        return redirect(url_for("manage_members"))

    return render_template(
        "admin/edit_member.html",
        member=member
    )

@app.route("/admin/members/add", methods=["GET", "POST"])
def add_member():

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()

    if request.method == "POST":
        name = request.form["name"]
        role = request.form["role"]
        member_type = request.form["type"]

        photo = request.files.get("photo")
        filename = ""

        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            upload_path = os.path.join("app", "static", "uploads", "members")
            os.makedirs(upload_path, exist_ok=True)
            photo.save(os.path.join(upload_path, filename))

        new_id = max([m["id"] for m in data["members"]], default=0) + 1

        data["members"].append({
            "id": new_id,
            "name": name,
            "role": role,
            "type": member_type,
            "photo": filename
        })

        save_data(data)
        flash("Member added successfully", "success")
        return redirect(url_for("manage_members"))

    return render_template("admin/add_member.html")

@app.route("/admin/members/delete/<int:member_id>")
def delete_member(member_id):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()
    member = next((m for m in data["members"] if m["id"] == member_id), None)

    if not member:
        flash("Member not found", "error")
        return redirect(url_for("manage_members"))

    # Delete photo if exists
    if member.get("photo"):
        photo_path = os.path.join(
            "app", "static", "uploads", "members", member["photo"]
        )
        if os.path.exists(photo_path):
            os.remove(photo_path)

    data["members"] = [m for m in data["members"] if m["id"] != member_id]
    save_data(data)

    flash("Member deleted successfully", "success")
    return redirect(url_for("manage_members"))

@app.route("/admin/gallery")
def manage_gallery():

    if session.get("role") not in ["content", "super"]:
        return redirect(url_for("login"))

    data = load_data()
    return render_template(
        "admin/gallery.html",
        gallery=data.get("gallery", [])
    )


from werkzeug.utils import secure_filename
import uuid

UPLOAD_THUMBNAIL_FOLDER = "app/static/uploads/gallery/thumbnails"

@app.route("/admin/gallery/add", methods=["GET", "POST"])
def add_gallery():

    if session.get("role") not in ["content", "super"]:
        return redirect(url_for("login"))

    data = load_data()

    if request.method == "POST":
        title = request.form["title"]
        thumbnail = request.files["thumbnail"]

        filename = secure_filename(thumbnail.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        thumbnail.save(os.path.join(UPLOAD_THUMBNAIL_FOLDER, unique_name))

        new_gallery = {
            "id": len(data["gallery"]) + 1,
            "slug": title.lower().replace(" ", "-"),
            "title": title,
            "thumbnail": unique_name,
            "images": []
        }

        data["gallery"].append(new_gallery)
        save_data(data)

        flash("Gallery event added successfully", "success")
        return redirect(url_for("manage_gallery"))

    return render_template("admin/add_gallery.html")

@app.route("/admin/gallery/delete/<int:gallery_id>")
def delete_gallery(gallery_id):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()

    gallery = next(
        (g for g in data["gallery"] if g["id"] == gallery_id),
        None
    )

    if not gallery:
        flash("Gallery not found", "error")
        return redirect(url_for("manage_gallery"))

    # OPTIONAL (recommended later): delete images from filesystem
    # shutil.rmtree(f"app/static/uploads/gallery/{gallery_id}", ignore_errors=True)

    data["gallery"] = [g for g in data["gallery"] if g["id"] != gallery_id]
    save_data(data)

    flash("Gallery deleted successfully", "success")
    return redirect(url_for("manage_gallery"))


@app.route("/admin/gallery/<int:gallery_id>", methods=["GET", "POST"])
def manage_gallery_images(gallery_id):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()
    gallery = next((g for g in data["gallery"] if g["id"] == gallery_id), None)

    if not gallery:
        flash("Gallery not found", "error")
        return redirect(url_for("manage_gallery"))

    images_path = os.path.join(
        "app", "static", "uploads", "gallery", str(gallery_id)
    )
    os.makedirs(images_path, exist_ok=True)

    if request.method == "POST":
        files = request.files.getlist("images")
        for file in files:
            if file.filename:
                file.save(os.path.join(images_path, file.filename))
        flash("Images uploaded successfully", "success")
        return redirect(url_for("manage_gallery_images", gallery_id=gallery_id))

    images = os.listdir(images_path)

    return render_template(
        "admin/gallery_images.html",
        gallery_id=gallery_id,
        images=images
    )

@app.route("/admin/gallery/edit/<int:gallery_id>", methods=["GET", "POST"])
def edit_gallery(gallery_id):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()
    gallery = next((g for g in data["gallery"] if g["id"] == gallery_id), None)

    if not gallery:
        flash("Gallery not found", "error")
        return redirect(url_for("manage_gallery"))

    if request.method == "POST":
        gallery["title"] = request.form["title"]

        thumbnail = request.files.get("thumbnail")
        if thumbnail and thumbnail.filename:
            filename = secure_filename(thumbnail.filename)
            thumb_path = os.path.join(
                "app", "static", "uploads", "gallery", "thumbnails", filename
            )
            thumbnail.save(thumb_path)
            gallery["thumbnail"] = filename   # 🔑 overwrite thumbnail

        save_data(data)
        flash("Gallery updated successfully", "success")
        return redirect(url_for("manage_gallery"))

    return render_template("admin/edit_gallery.html", gallery=gallery)


@app.route("/admin/gallery/<int:gallery_id>/upload", methods=["POST"])
def upload_gallery_image(gallery_id):

    if session.get("role") not in ["content", "super"]:
        return redirect(url_for("login"))

    data = load_data()
    gallery = next((g for g in data["gallery"] if g["id"] == gallery_id), None)

    if not gallery:
        return redirect(url_for("manage_gallery"))

    image = request.files["image"]
    filename = secure_filename(image.filename)

    event_folder = os.path.join(
        "app/static/uploads/gallery/events",
        gallery["slug"]
    )

    os.makedirs(event_folder, exist_ok=True)

    image.save(os.path.join(event_folder, filename))

    gallery["images"].append(filename)
    save_data(data)

    flash("Image uploaded successfully", "success")
    return redirect(url_for("manage_gallery_images", gallery_id=gallery_id))

@app.route("/admin/gallery/<int:gallery_id>/delete-image/<filename>")
def delete_gallery_image(gallery_id, filename):

    if session.get("role") != "content":
        return redirect(url_for("login"))

    data = load_data()

    gallery = next(
        (g for g in data["gallery"] if g["id"] == gallery_id),
        None
    )

    if not gallery:
        flash("Gallery not found", "error")
        return redirect(url_for("manage_gallery"))

    # 1️⃣ Remove image from JSON
    if filename in gallery["images"]:
        gallery["images"].remove(filename)

    # 2️⃣ Delete file from disk
    image_path = os.path.join(
        "app",
        "static",
        "uploads",
        "gallery",
        str(gallery_id),
        filename
    )

    if os.path.exists(image_path):
        os.remove(image_path)

    save_data(data)

    flash("Image deleted successfully", "success")
    return redirect(url_for("manage_gallery_images", gallery_id=gallery_id))

@app.route("/gallery/<slug>")
def view_gallery_event(slug):

    data = load_data()
    gallery = next((g for g in data["gallery"] if g["slug"] == slug), None)

    if not gallery:
        return redirect(url_for("gallery"))

    return render_template(
        "gallery_event.html",
        gallery=gallery
    )

@app.route("/gallery/<int:gallery_id>")
def view_gallery(gallery_id):

    data = load_data()

    gallery = next(
        (g for g in data["gallery"] if g["id"] == gallery_id),
        None
    )

    if not gallery:
        return render_template("404.html"), 404

    return render_template(
        "gallery_view.html",
        gallery=gallery
    )
