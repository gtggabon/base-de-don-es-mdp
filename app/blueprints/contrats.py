from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import Contrat, Etablissement

contrats_bp = Blueprint('contrats', __name__, url_prefix='/contrats')

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
UPLOAD_FOLDER = 'uploads/contrats'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@contrats_bp.route('/', methods=['GET'])
@login_required
def index():
    """Liste tous les contrats avec pagination et filtrage"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    statut = request.args.get('statut', '')
    etablissement_id = request.args.get('etablissement_id', '')
    
    query = Contrat.query
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                Contrat.reference.ilike(f'%{search}%'),
                Contrat.type_abonnement.ilike(f'%{search}%')
            )
        )
    
    if statut:
        query = query.filter(Contrat.statut == statut)
    
    if etablissement_id:
        query = query.filter(Contrat.etablissement_id == int(etablissement_id))
    
    # Pagination
    pagination = query.order_by(desc(Contrat.date_creation)).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    contrats = pagination.items
    etablissements = Etablissement.query.all()
    
    return render_template(
        'contrats/index.html',
        contrats=contrats,
        pagination=pagination,
        etablissements=etablissements,
        search=search,
        statut=statut,
        etablissement_id=etablissement_id
    )


@contrats_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Créer un nouveau contrat"""
    if request.method == 'POST':
        try:
            # Validation des données
            reference = request.form.get('reference')
            etablissement_id = request.form.get('etablissement_id')
            type_abonnement = request.form.get('type_abonnement')
            montant = request.form.get('montant')
            date_debut = request.form.get('date_debut')
            date_fin = request.form.get('date_fin')
            statut = request.form.get('statut', 'ACTIF')
            
            # Vérifier l'unicité de la référence
            if Contrat.query.filter_by(reference=reference).first():
                flash('Cette référence existe déjà', 'error')
                return redirect(url_for('contrats.create'))
            
            # Créer le contrat
            contrat = Contrat(
                reference=reference,
                etablissement_id=int(etablissement_id),
                type_abonnement=type_abonnement,
                montant=float(montant),
                statut=statut
            )
            
            if date_debut:
                contrat.date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            
            if date_fin:
                contrat.date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            
            # Gestion du fichier PDF
            if 'fichier_pdf' in request.files:
                file = request.files['fichier_pdf']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{reference}_{datetime.now().timestamp()}_{file.filename}")
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    contrat.fichier_pdf = filename
            
            db.session.add(contrat)
            db.session.commit()
            
            flash(f'Contrat {reference} créé avec succès', 'success')
            return redirect(url_for('contrats.view', id=contrat.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    etablissements = Etablissement.query.all()
    return render_template('contrats/create.html', etablissements=etablissements)


@contrats_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id):
    """Afficher les détails d'un contrat"""
    contrat = Contrat.query.get_or_404(id)
    return render_template('contrats/view.html', contrat=contrat)


@contrats_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier un contrat"""
    contrat = Contrat.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            contrat.reference = request.form.get('reference')
            contrat.type_abonnement = request.form.get('type_abonnement')
            contrat.montant = float(request.form.get('montant'))
            contrat.statut = request.form.get('statut')
            
            date_debut = request.form.get('date_debut')
            if date_debut:
                contrat.date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            
            date_fin = request.form.get('date_fin')
            if date_fin:
                contrat.date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            
            # Gestion du nouveau fichier
            if 'fichier_pdf' in request.files:
                file = request.files['fichier_pdf']
                if file and allowed_file(file.filename):
                    # Supprimer l'ancien fichier
                    if contrat.fichier_pdf:
                        try:
                            os.remove(os.path.join(UPLOAD_FOLDER, contrat.fichier_pdf))
                        except:
                            pass
                    
                    filename = secure_filename(f"{contrat.reference}_{datetime.now().timestamp()}_{file.filename}")
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    contrat.fichier_pdf = filename
            
            db.session.commit()
            flash(f'Contrat {contrat.reference} modifié avec succès', 'success')
            return redirect(url_for('contrats.view', id=contrat.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    return render_template('contrats/edit.html', contrat=contrat)


@contrats_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer un contrat"""
    contrat = Contrat.query.get_or_404(id)
    
    try:
        # Supprimer le fichier
        if contrat.fichier_pdf:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, contrat.fichier_pdf))
            except:
                pass
        
        reference = contrat.reference
        db.session.delete(contrat)
        db.session.commit()
        flash(f'Contrat {reference} supprimé avec succès', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('contrats.index'))


@contrats_bp.route('/api/stats', methods=['GET'])
@login_required
def stats():
    """API pour les statistiques des contrats"""
    total = Contrat.query.count()
    actifs = Contrat.query.filter_by(statut='ACTIF').count()
    inactifs = Contrat.query.filter_by(statut='INACTIF').count()
    montant_total = db.session.query(db.func.sum(Contrat.montant)).scalar() or 0
    
    return jsonify({
        'total': total,
        'actifs': actifs,
        'inactifs': inactifs,
        'montant_total': float(montant_total)
    })
