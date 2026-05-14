from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import Etablissement, User, Contrat

etablissements_bp = Blueprint('etablissements', __name__, url_prefix='/etablissements')

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads/logos'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@etablissements_bp.route('/', methods=['GET'])
@login_required
def index():
    """Liste tous les établissements avec pagination et filtrage"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    type_etablissement = request.args.get('type', '')
    statut = request.args.get('statut', '')
    
    query = Etablissement.query
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                Etablissement.nom.ilike(f'%{search}%'),
                Etablissement.code.ilike(f'%{search}%'),
                Etablissement.email.ilike(f'%{search}%')
            )
        )
    
    if type_etablissement:
        query = query.filter(Etablissement.type_etablissement == type_etablissement)
    
    if statut == 'actif':
        query = query.filter(Etablissement.actif == True)
    elif statut == 'inactif':
        query = query.filter(Etablissement.actif == False)
    
    # Pagination
    pagination = query.order_by(desc(Etablissement.date_creation)).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    etablissements = pagination.items
    
    return render_template(
        'etablissements/index.html',
        etablissements=etablissements,
        pagination=pagination,
        search=search,
        type_etablissement=type_etablissement,
        statut=statut
    )


@etablissements_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Créer un nouvel établissement"""
    if request.method == 'POST':
        try:
            # Validation des données
            nom = request.form.get('nom')
            code = request.form.get('code')
            
            # Vérifier l'unicité du code
            if Etablissement.query.filter_by(code=code).first():
                flash('Ce code d\'établissement existe déjà', 'error')
                return redirect(url_for('etablissements.create'))
            
            # Créer l'établissement
            etablissement = Etablissement(
                nom=nom,
                code=code,
                telephone=request.form.get('telephone'),
                whatsapp=request.form.get('whatsapp'),
                email=request.form.get('email'),
                adresse=request.form.get('adresse'),
                ville=request.form.get('ville'),
                pays=request.form.get('pays', 'Gabon'),
                site_web=request.form.get('site_web'),
                responsable=request.form.get('responsable'),
                type_etablissement=request.form.get('type_etablissement'),
                nombre_eleves=request.form.get('nombre_eleves', type=int),
                type_abonnement=request.form.get('type_abonnement')
            )
            
            date_expiration = request.form.get('date_expiration')
            if date_expiration:
                etablissement.date_expiration = datetime.strptime(date_expiration, '%Y-%m-%d').date()
            
            # Gestion du logo
            if 'logo' in request.files:
                file = request.files['logo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{code}_{datetime.now().timestamp()}_{file.filename}")
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    etablissement.logo = filename
            
            db.session.add(etablissement)
            db.session.commit()
            
            flash(f'Établissement {nom} créé avec succès', 'success')
            return redirect(url_for('etablissements.view', id=etablissement.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    return render_template('etablissements/create.html')


@etablissements_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id):
    """Afficher les détails d'un établissement"""
    etablissement = Etablissement.query.get_or_404(id)
    users = User.query.filter_by(etablissement_id=id).all()
    contrats = Contrat.query.filter_by(etablissement_id=id).all()
    
    return render_template(
        'etablissements/view.html',
        etablissement=etablissement,
        users=users,
        contrats=contrats
    )


@etablissements_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier un établissement"""
    etablissement = Etablissement.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            etablissement.nom = request.form.get('nom')
            etablissement.telephone = request.form.get('telephone')
            etablissement.whatsapp = request.form.get('whatsapp')
            etablissement.email = request.form.get('email')
            etablissement.adresse = request.form.get('adresse')
            etablissement.ville = request.form.get('ville')
            etablissement.pays = request.form.get('pays', 'Gabon')
            etablissement.site_web = request.form.get('site_web')
            etablissement.responsable = request.form.get('responsable')
            etablissement.type_etablissement = request.form.get('type_etablissement')
            etablissement.nombre_eleves = request.form.get('nombre_eleves', type=int)
            etablissement.type_abonnement = request.form.get('type_abonnement')
            etablissement.actif = request.form.get('actif') == 'on'
            etablissement.abonnement_actif = request.form.get('abonnement_actif') == 'on'
            
            date_expiration = request.form.get('date_expiration')
            if date_expiration:
                etablissement.date_expiration = datetime.strptime(date_expiration, '%Y-%m-%d').date()
            
            # Gestion du nouveau logo
            if 'logo' in request.files:
                file = request.files['logo']
                if file and allowed_file(file.filename):
                    if etablissement.logo:
                        try:
                            os.remove(os.path.join(UPLOAD_FOLDER, etablissement.logo))
                        except:
                            pass
                    
                    filename = secure_filename(f"{etablissement.code}_{datetime.now().timestamp()}_{file.filename}")
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    etablissement.logo = filename
            
            db.session.commit()
            flash(f'Établissement {etablissement.nom} modifié avec succès', 'success')
            return redirect(url_for('etablissements.view', id=etablissement.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    return render_template('etablissements/edit.html', etablissement=etablissement)


@etablissements_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer un établissement"""
    etablissement = Etablissement.query.get_or_404(id)
    
    try:
        # Supprimer le logo
        if etablissement.logo:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, etablissement.logo))
            except:
                pass
        
        nom = etablissement.nom
        db.session.delete(etablissement)
        db.session.commit()
        flash(f'Établissement {nom} supprimé avec succès', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('etablissements.index'))


@etablissements_bp.route('/api/stats', methods=['GET'])
@login_required
def stats():
    """API pour les statistiques des établissements"""
    total = Etablissement.query.count()
    actifs = Etablissement.query.filter_by(actif=True).count()
    abonnement_actifs = Etablissement.query.filter_by(abonnement_actif=True).count()
    
    return jsonify({
        'total': total,
        'actifs': actifs,
        'abonnement_actifs': abonnement_actifs
    })
