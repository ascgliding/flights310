#!/bin/bash

#cd /home/rayb/PycharmProjects/flask3_10/asc

echo "Remove refernces to wtorms.fields.html5"
sed -i 's/wtforms\.fields\.html5/wtforms\.fields/g' *.py

# add markupsafe
echo "remove HTML5String from wtforms_ext"
sed -i 's/\(^from wtforms\.widgets.*\)\(, HTMLString\)/\1/' wtforms_ext.py

echo "add Marksupsafe to wtforms_ext"
sed -i '/^from wtforms\.widgets.*/a from markupsafe import Markup' wtforms_ext.py

echo "change HTML5String to Markupsafe in wtforms_ext"
sed -i 's/HTMLString/Markup/' wtforms_ext.py

echo "change HTML5String to Markupsafe in membership.py"
sed -i 's/HTMLString/Markup/' membership.py

echo "add email_validator to membership.py"
sed -i '/from flask_wtf import Form/a import email_validator' membership.py

echo "Remove unused reference in membership.py"
sed -i 's/from wtforms.ext.sqlalchemy.orm import model_form/#\0/' membership.py


echo "Do not forget to run pip install -r REQUIREMENTS_3_10.txt"




