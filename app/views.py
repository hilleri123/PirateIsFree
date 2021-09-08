
from flask import render_template, flash, redirect, session, url_for, request, g
from app import app

from .collect_playlist import *
from .forms import MyForm


@app.route('/', methods=['GET', 'POST'])
def index():
    form = MyForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.cancel.data:
                return ('', 204)
            all_text = form.body.data.replace('\r', '')
            link_list = [i for i in all_text.split('\n') if not i.startswith('#') and len(i) > 0 and i.endswith('.ts')]
            download_link_list(link_list, form.file_name.data)

    return render_template("storage.html", form = form)


