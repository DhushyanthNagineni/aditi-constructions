from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired

class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Project image')
    submit = SubmitField('Upload')

class TestimonialForm(FlaskForm):
    customer_name = StringField('Customer name', validators=[DataRequired()])
    content = TextAreaField('Testimonial', validators=[DataRequired()])
    photo = FileField('Customer photo')
    submit = SubmitField('Upload')

class OfferForm(FlaskForm):
    title = StringField('Offer title', validators=[DataRequired()])
    details = TextAreaField('Details', validators=[DataRequired()])
    submit = SubmitField('Save Offer')