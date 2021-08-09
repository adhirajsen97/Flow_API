import pandas as pd
import os, csv, sys, uuid, werkzeug, webbrowser
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for, send_from_directory



UPLOAD_DIRECTORY = "api_uploaded_files"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    app = Flask(__name__, template_folder=template_folder)
else:
    api = Flask(__name__)
api.config["CLIENT_CSV"] = UPLOAD_DIRECTORY

@api.route('/', methods=['GET'])
def index():
    return redirect(url_for('uploader'))

@api.route('/upload', methods=['GET', 'POST'])
def uploader():

    message='Please Upload a CSV or XLSX file'
    columns=[]
    col=[]

    if request.method == 'POST':
        if request.files['doc_file'].filename == '':
            message = 'No File Uploaded, Upload a CSV or XLSX file'
        else:
            uploaded_file = request.files['doc_file']
            #uploaded_file.save()
            uid = uuid.uuid1()
            uid_filename = "{}".format(uid)+".csv"
            uploaded_file.save(os.path.join(UPLOAD_DIRECTORY, uid_filename))
            return redirect(url_for("get_param", uid=uid))
            
    return  render_template('upload.html', message=message, columns=columns, col=col)

@api.route("/transpose/<uid>", methods=['GET','POST'])
def get_param(uid):
    if os.path.join(api.config["CLIENT_CSV"], "{}".format(uid)+".csv"):
        message = 'File Imported Successfully'
        columns=[]
        col=[]
        uid_filename = "{}".format(uid)+".csv"
        data = pd.read_csv(os.path.join(api.config["CLIENT_CSV"], uid_filename), header = 0, low_memory = False)
        columns = [i for i in data.columns]

        if request.method == 'POST':
            if request.form.getlist('ids[]'):
                if request.form.getlist('vars[]') or (request.form.get('from')and request.form.get('to')):
                    if request.form.getlist('vars[]'):
                        col_var= request.form.getlist('vars[]')
                    else:
                        frm = request.form.get('from')
                        to = request.form.get('to')
                        frm = int(frm)-1
                        to = int(to)-1
                        df_var = data.iloc[:, frm:to]
                        col_var = [i for i in df_var.columns]
                    
                    col_id = request.form.getlist('ids[]')

                    for c in col_id:
                        if c in col_var:
                            message = "Error! Try Again."
                            return render_template('transpose.html', message=message, columns=columns, col=col)
                    
                    key = request.form.get('key')
                    value = request.form.get('value')
                    #print("cols",cols, "key", key, "value", value)
                    if not key:
                        key="Variable"
                    if not value:
                        value="Value"
                    df = gather(data, key, value, col_id, col_var)
                    Tuid = uuid.uuid1()
                    Tuid_filename = "Transposed_File_"+"{}".format(Tuid)+".csv"
                    
                    df.to_csv(os.path.join(api.config["CLIENT_CSV"], Tuid_filename), sep=',', encoding='utf-8', index = False)
                    message='File Transposed Successfully'
                    return redirect(url_for('view_dwld',Tuid_filename=Tuid_filename))
                else:
                    message = "Please Select Columns to Transpose"
            else:
                message = "Please Select IDS/Columns as Index"
    else:
        abort(404)

    return render_template('transpose.html', message=message, columns=columns, col=col)

def gather(df, key, value, cols, var_cols):
    id_vars = cols
    value_vars = var_cols
    var_name = key
    value_name = value
    return pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name )

@api.route("/view/<path:Tuid_filename>", methods=["GET", "POST"])
def view_dwld(Tuid_filename):
    message = 'File Transposed Successfully'

    if os.path.join(api.config["CLIENT_CSV"], Tuid_filename):
        df = pd.read_csv(os.path.join(api.config["CLIENT_CSV"], Tuid_filename), header = 0, low_memory = False, index_col = False)
        df = df.head(10)
        if request.method=="POST":
            try:
                return send_from_directory(directory=api.config["CLIENT_CSV"], path=Tuid_filename, as_attachment=True)
            except FileNotFoundError:
                abort(404)
    else:
        abort(404)
    return render_template('download.html', message=message,tables=[df.to_html(classes='data', header="true")], titles=df.columns.values) 




if __name__ == "__main__":
    webbrowser.open_new('http://127.0.0.1:5000/')
    api.run(debug=True)