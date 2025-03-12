from asc.schema import Queries
from flask import (
    Blueprint,  render_template,  session, send_file, request, g, redirect, url_for, current_app, flash
)

from sqlalchemy import text as sqltext

from asc import db

# WTforms
from flask_wtf import FlaskForm
from wtforms import  StringField, SubmitField, TextAreaField, IntegerField

bp = Blueprint('qryviewer', __name__,template_folder='templates/qryviewer')
app = current_app
applog = app.logger


class QryEditForm(FlaskForm):
    name = 'Query Editor'
    id = IntegerField("ID", description="Rowid", render_kw={"disabled": True})
    shortname = StringField('Short Name', description='Just a name to assign to the query')
    pagetitle = StringField('Page Title', description='The name that will appear at the top of the page')
    querysql = TextAreaField('SQL',description="Sql Statement to run", render_kw={"rows":12})
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})

@bp.route('/qrylist')
##@bp.route('/table_rows/<tablename>/<int:page>')
##def table_rows(tablename,page=1):
def qrylist():
    thisqry = Queries.query.all()
    return render_template('qryviewer/qrylist.html', list=thisqry)

@bp.route('/qrymaint/<id>', methods=['GET','POST'])
##@bp.route('/table_rows/<tablename>/<int:page>')
##def table_rows(tablename,page=1):
def qrymaint(id):
    thisrow = db.session.get(Queries,id)
    if thisrow is None:
        thisrow = Queries()
    thisform = QryEditForm(obj=thisrow)
    if thisform.cancel.data:
        return redirect(url_for('qryviewer.qrylist'))
    if request.method == "POST":
        if thisform.validate_on_submit():
            if thisform.delete.data:
                try:
                    db.session.delete(thisrow)
                    db.session.commit()
                except Exception as e:
                    applog.error(str(e))
                    flash(
                        "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                        "error")
                    applog.info('DELETE:' + repr(thisrow))
                    return redirect(url_for('qryviewer.qrylist'))
            # must be in add or update if here
            thisform.populate_obj(thisrow)
            try:
                if thisrow.id is None:  # must be add new row
                    db.session.add(thisrow)
                    applog.info('ADD:' + repr(thisrow))
                else:
                    applog.info('UPDATE:' + repr(thisrow))
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('qryviewer.qrylist'))
            # this line occurs of either request.method is 'GET' or the validate_on_submit fails

    return render_template('qryviewer/qrymaint.html', form=thisform)

@bp.route('/qryviewer/<id>')
##@bp.route('/table_rows/<tablename>/<int:page>')
##def table_rows(tablename,page=1):
def qryviewer(id):
    thisqry = db.session.get(Queries,id)
    data = db.engine.execute(thisqry.querysql).fetchall()
    thishtml = '<div class="table">  <div class="row">'
    # add the column headings
    for k in db.engine.execute(thisqry.querysql).keys():
        thishtml = f'{thishtml} <div class="heading"> {k} </div>'
    thishtml = f'{thishtml}  </div> '
    # Add the data
    for row in data:
        thishtml = f'{thishtml} <div class="row"> '
        for dataitem in row:
            thishtml = f'{thishtml} <div class="cell"> {dataitem} </div>'
        thishtml = f'{thishtml} </div> '
    thishtml = f'{thishtml}  </div> '
    return render_template('qryviewer/qryviewer.html', pagetitle=thisqry.pagetitle, tablehtml=thishtml)

