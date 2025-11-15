import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory, jsonify, session
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from config import Config
from models import db, Project, Testimonial, Offer, AdminUser, Consultation
from forms import ProjectForm, TestimonialForm, OfferForm

ALLOWED = Config.ALLOWED_EXTENSIONS


def allowed_file(filename):
    return (
        bool(filename)
        and '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED
    )


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('admin_user_id') is None:
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Create default admin if none exists
        admin_user_env = os.environ.get('ADMIN_USER')
        admin_pass_env = os.environ.get('ADMIN_PASS')
        existing_admin = AdminUser.query.first()
        if not existing_admin:
            username = admin_user_env or 'admin'
            password = admin_pass_env or 'admin'
            hashed = generate_password_hash(password)
            admin = AdminUser(username=username, password_hash=hashed)
            db.session.add(admin)
            db.session.commit()
            app.logger.warning(
                f'No admin found — created default admin "{username}". '
                f'PLEASE change the password (ADMIN_PASS) for production.'
            )

    @app.context_processor
    def inject_now():
        # so you can use {{ now().year }} in templates
        return {'now': datetime.utcnow}

    # ---------- PUBLIC ROUTES ----------

    @app.route('/')
    def index():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
        offers = Offer.query.filter(Offer.active == True).all()
        return render_template('index.html',
                               projects=projects,
                               testimonials=testimonials,
                               offers=offers)

    @app.route('/projects')
    def projects_page():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/consultation', methods=['POST'])
    def book_consultation():
        """Handle 'Book Consultation' / contact form submissions (public)."""
        name = request.form.get('name') or ''
        email = request.form.get('email') or ''
        phone = request.form.get('phone') or ''
        message = request.form.get('message') or ''

        if not name.strip() or not email.strip():
            flash('Please provide at least your name and email.', 'danger')
            return redirect(url_for('index') + '#contact')

        c = Consultation(
            name=name.strip(),
            email=email.strip(),
            phone=phone.strip() if phone else '',
            message=message.strip() if message else ''
        )
        db.session.add(c)
        db.session.commit()

        flash('Thank you! Your consultation request has been received. We will contact you soon.', 'success')
        return redirect(url_for('index') + '#contact')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/api/active-offers')
    def active_offers_api():
        offers = Offer.query.filter(Offer.active == True).all()
        data = [{'id': o.id, 'title': o.title, 'details': o.details} for o in offers]
        return jsonify(data)

    # ---------- AUTH / ADMIN ROUTES ----------

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = AdminUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session.clear()
                session['admin_user_id'] = user.id
                flash('Logged in successfully.', 'success')
                next_url = request.args.get('next') or url_for('admin')
                return redirect(next_url)
            flash('Invalid username or password.', 'danger')
        return render_template('admin_login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_user_id', None)
        flash('Logged out.', 'success')
        return redirect(url_for('admin_login'))

    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin():
        pform = ProjectForm()
        tform = TestimonialForm()
        oform = OfferForm()

        projects = Project.query.order_by(Project.created_at.desc()).all()
        testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
        offers = Offer.query.order_by(Offer.id.desc()).all()
        consultations = Consultation.query.order_by(Consultation.created_at.desc()).all()

        form_name = request.form.get('form_name')

        # ---- PROJECT UPLOAD ----
        if request.method == 'POST' and form_name == 'project':
            if pform.validate_on_submit():
                f = request.files.get('image')
                filename = None
                if f and f.filename:
                    if allowed_file(f.filename):
                        filename = secure_filename(f.filename)
                        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    else:
                        flash('Invalid image type. Allowed: jpg, jpeg, png, gif, webp', 'danger')
                        return redirect(url_for('admin'))

                proj = Project(
                    title=pform.title.data,
                    description=pform.description.data,
                    image_filename=filename
                )
                db.session.add(proj)
                db.session.commit()
                flash('Project uploaded', 'success')
                return redirect(url_for('admin'))

        # ---- TESTIMONIAL UPLOAD ----
        if request.method == 'POST' and form_name == 'testimonial':
            if tform.validate_on_submit():
                f = request.files.get('photo')
                filename = None
                if f and f.filename:
                    if allowed_file(f.filename):
                        filename = secure_filename(f.filename)
                        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    else:
                        flash('Invalid photo type. Allowed: jpg, jpeg, png, gif, webp', 'danger')
                        return redirect(url_for('admin'))

                t = Testimonial(
                    customer_name=tform.customer_name.data,
                    content=tform.content.data,
                    photo_filename=filename
                )
                db.session.add(t)
                db.session.commit()
                flash('Testimonial uploaded', 'success')
                return redirect(url_for('admin'))

        # ---- OFFER CREATE ----
        if request.method == 'POST' and form_name == 'offer':
            if oform.validate_on_submit():
                o = Offer(
                    title=oform.title.data,
                    details=oform.details.data,
                    active=True
                )
                db.session.add(o)
                db.session.commit()
                flash('Offer saved', 'success')
                return redirect(url_for('admin'))

        return render_template(
            'admin.html',
            pform=pform,
            tform=tform,
            oform=oform,
            projects=projects,
            testimonials=testimonials,
            offers=offers,
            consultations=consultations
        )

    # ----- DELETE ROUTES -----

    @app.route('/admin/delete/project/<int:project_id>', methods=['POST'])
    @login_required
    def delete_project(project_id):
        proj = Project.query.get_or_404(project_id)
        if proj.image_filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], proj.image_filename)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        db.session.delete(proj)
        db.session.commit()
        flash('Project deleted successfully.', 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/delete/testimonial/<int:testimonial_id>', methods=['POST'])
    @login_required
    def delete_testimonial(testimonial_id):
        t = Testimonial.query.get_or_404(testimonial_id)
        if t.photo_filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], t.photo_filename)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        db.session.delete(t)
        db.session.commit()
        flash('Testimonial deleted successfully.', 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/delete/offer/<int:offer_id>', methods=['POST'])
    @login_required
    def delete_offer(offer_id):
        o = Offer.query.get_or_404(offer_id)
        db.session.delete(o)
        db.session.commit()
        flash('Offer deleted successfully.', 'success')
        return redirect(url_for('admin'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)

