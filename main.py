from flask import Flask, render_template,request
import uuid
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'user_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create",methods=["GET","POST"])
def create():
    myid = uuid.uuid1()
    if(request.method == "POST"):
        rec_id = request.form.get("uuid")
        desc = request.form.get("text")
        for key,values in request.files.items():
            print(key,values)
            file = request.files[key]
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], rec_id)
            os.makedirs(upload_path, exist_ok=True)
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],rec_id,filename))

            with open(os.path.join(app.config['UPLOAD_FOLDER'], rec_id, "description"),"w") as f:
                f.write(desc)

    return render_template("create.html", myid = myid)

@app.route("/gallery")
def gallery():
    reels = os.listdir("static/reels")
    return render_template("gallery.html",reels = reels)

app.run(debug=True)