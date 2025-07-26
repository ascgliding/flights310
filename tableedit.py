# ----------------------------------------------------------------------------------
# this is a generic editor that will maintain data from any table
# using sqlalchemy and WTforms.
# Some rules:
#    Each class defined in the schema must implement __str__ for each row.
#        This is what appears on the row selection screen
#    Each field in the schema should define "comment" - this appears as the field prompt.
#    Each row must have a primary key that is a single field.
#
# Before use in any given project you need to review the lines that have the comment
# REVIEW THIS:
# in the line immediately before

# the entry url for this is:
#      <p><a href="{{ url_for('tableedit.table_select') }}">Data Editor</a></p>
# blueprint registration will look like this:
# Register the database table editor :
#   from . import tableedit
#   app.register_blueprint(tableedit.bp)
# ----------------------------------------------------------------------------------


from flask import (
    Blueprint, flash, render_template,  session, send_file, request, g, redirect, url_for, current_app
)
from flask_login import login_required

# WTforms
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField, DecimalField, Field, FieldList, ValidationError, DateTimeField, TimeField
from wtforms.fields import EmailField, IntegerField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, optional, Regexp
import sqlalchemy

# REVIEW THIS:
from asc import db

bp = Blueprint('tableedit', __name__,template_folder='templates/tableedit')
app = current_app
applog = app.logger

def get_table_list():
    """
    This function should be modified to return a list of tables according
    to your particular schemal
    :return: A list of strings being the table names
    """
    # REVIEW THIS:
    returnlist = [s.__name__ for s in db.Model.__subclasses__()]
    returnlist.sort()
    return returnlist

def get_one_table_object(tablename):
    """
    This function is passed a string containing the name of a table as defined in a
    SQLAlchemy schema.  It returns a table object.
    :param tablname: the string containing the name
    :return: an object which corresponds to the name
    """
    # there are two different subclasses so each needs to be checked individually
    # REVIEW THIS:
    if tablename in [s.__name__ for s in db.Model.__subclasses__()]:
        return [f for f in db.Model.__subclasses__() if f.__name__ == tablename][0]
    return None

def get_primary_key(table_obj):
    """
    Returns an object which is the primary key for the table
    :param table_obj: An sqlAlchemy table object
    :return: primary key object
    """
    for pk in [pk for pk in table_obj.__dict__]:
        fld = table_obj.__dict__.get(pk)
        if isinstance(fld, sqlalchemy.orm.attributes.InstrumentedAttribute):
            if fld.primary_key:
                return fld
    return None

def get_columns(tableobj,fieldlist=[]):
    """
    This function returns a list of fields that can be maintained on the table.
    :param tableobj: The sqlAlchemy object
    :param fieldlist: An optional list containing the fields that are to be placed on the form.
    :return: A list of dictionaries containing the fields and their Data types
    """
    cols = []
    for c in [c for c in tableobj.__dict__]:
        thing = tableobj.__dict__.get(c)
        # try:
        #     print(thing, type(thing))
        # except Exception as e:
        #     pass
        if isinstance(thing, sqlalchemy.orm.attributes.InstrumentedAttribute):
            try:
                if thing.comment is not None:
                    if len(thing.comment) > 30:
                        fldprompt = thing.name
                        hoverhelp = thing.comment
                    else:
                        fldprompt = thing.comment
                        hoverhelp = f'fieldname is {thing.name}.  Database type is {str(thing.type)}'
                else:
                    fldprompt = thing.name
                    hoverhelp = thing.name
                datatype = thing.type.python_type.__name__
                # print(f'{thing.name}: {thing.type}' Python: {datatype})
                # override the data type if it's sqlalchemy text
                if isinstance(thing.type,sqlalchemy.Text):
                    datatype = 'text'
                cols.append({'col':thing.name, 'type': datatype,  'name':thing.name, 'prompt':fldprompt, 'hoverhelp':hoverhelp})
            except Exception as e:
                pass  # just ignore those we don't ahve a data type for.
    return cols


class TableEditForm(FlaskForm):
    name = 'Table Maintenance'
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "return ConfirmDelete()"})

@bp.route('/table_select', methods=['GET', 'POST'])
@login_required
def table_select():
    return render_template('table_select.html', list=get_table_list())


@bp.route('/table_rows/<tablename>')
@bp.route('/table_rows/<tablename>/<int:page>')
@login_required
def table_rows(tablename,page=1):
    # Note that we assume that every table defined in the schema has a valied str() defined
    thistable = get_one_table_object(tablename)
    pk = get_primary_key(thistable)
    # we know the primary key because it is the field with the boolean "primary_key" set to true
    # REVIEW THIS
    thispage = db.paginate(db.select(thistable).order_by(pk), page=page, per_page=15, error_out=False)
    displaylist = []
    for t in thispage:
        displaylist.append((getattr(t,pk.name),str(t)))
    return render_template('tableedit/table_rows.html', table=tablename, rows=thispage,list=displaylist)


@bp.route('/table_edit', methods=['GET', 'POST'])
@bp.route('/table_edit/<tablename>', methods=['GET', 'POST'])
@bp.route('/table_edit/<tablename>/<rowid>', methods=['GET', 'POST'])
@login_required
def table_edit(tablename,rowid=None):
    class ThisViewForm(TableEditForm):
        pass

    thistable = get_one_table_object(tablename)
    #REVIEW THIS
    thisrec = db.session.get(thistable,rowid)
    if thisrec is None:
        thisrec = thistable()
    # Here we need to add all the fields
    skippedfields = []
    for f in get_columns(thistable):
        if f['name'] == get_primary_key(thistable).name:
            setattr(ThisViewForm,f['name'], StringField(f['prompt'], [validators.optional()],
                                                   description=f['hoverhelp'], render_kw={'disabled':True, 'style':'border:None'}))

        elif f['type'] == 'int':
            setattr(ThisViewForm,f['name'], IntegerField(f['prompt'], [validators.optional()],
                                                   description=f['hoverhelp']))
        elif f['type'] == 'str' :
            setattr(ThisViewForm,f['name'], StringField(f['prompt'], [validators.optional()],
                                                   description=f['hoverhelp']))
        elif f['type'] == 'bool':
            setattr(ThisViewForm, f['name'], BooleanField(f['prompt'], [validators.optional()],
                                                 description=f['hoverhelp']))
        elif f['type'] == 'date':
            setattr(ThisViewForm, f['name'], DateField(f['prompt'], [validators.optional()],
                                                          description=f['hoverhelp']))
        elif f['type'] == 'Decimal':
            setattr(ThisViewForm, f['name'], DecimalField(f['prompt'], [validators.optional()],
                                                       description=f['hoverhelp']))
        elif f['type'] == 'datetime':
            setattr(ThisViewForm, f['name'], DateTimeField(f['prompt'], [validators.optional()],
                                                          description=f['hoverhelp']))
        elif f['type'] == 'time':
            setattr(ThisViewForm, f['name'], TimeField(f['prompt'], [validators.optional()],
                                                           description=f['hoverhelp']))
        elif f['type'] == 'text':
            setattr(ThisViewForm, f['name'], TextAreaField(f['prompt'], [validators.optional()],
                                                       description=f['hoverhelp'],
                                                        render_kw={'rows':5, 'cols':50}))
        else:
            # keep track of any fields we missed.  A trap for their data type will need to appear above.
            skippedfields.append(f'{f["name"]} ({f["type"]}) ')
    thisform = ThisViewForm(obj=thisrec)
    thisform.name = tablename + ' Maintenance'
    print(",".join(skippedfields))

    if request.method == 'POST' and thisform.validate():
        if thisform.cancel.data:
            return redirect(url_for('tableedit.table_rows', tablename=tablename))
        if thisform.delete.data:
            try:
                # REVIEW THIS
                db.session.delete(thisrec)
                applog.info('DELETE:' + repr(thisrec))
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('tableedit.table_rows', tablename=tablename))
        thisform.populate_obj(thisrec)
        if thisrec.rowid is None:
            #REVIEW THIS
            db.session.add(thisrec)
            applog.info('ADD:' + repr(thisrec))
        applog.info('UPDATE:' + repr(thisrec))
        try:
            # REVIEW THIS
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('tableedit.table_rows', tablename=tablename))
    return render_template('tableedit/table_edit.html', form=thisform, skipped=",".join(skippedfields))