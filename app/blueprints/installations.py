from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from datetime import datetime

from extensions import db
from models import Installation, Etablissement, User

installations_bp = Blueprint('installations', __name__, url_prefix='/installations')


@installations_bp.route('/', methods=['GET'])
@login_required
def index():
    """Liste toutes les installations avec pagination et filtrage"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    statut = request.args.get('statut', '')
    type_installation = request.args.get('type', '')
    
    query = Installation.query
    
    # Appliquer les filtres
    if search:
        query = query.join(Etablissement).filter(
            Etablissement.nom.ilike(f'%{search}%')
        )
    
    if statut:
        query = query.filter(Installation.statut == statut)
    
    if type_installation:
        query = query.filter(Installation.type_installation == type_installation)
    
    # Pagination
    pagination = query.order_by(desc(Installation.date_installation)).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    installations = pagination.items
    
    return render_template(
        'installations/index.html',
        installations=installations,
        pagination=pagination,
        search=search,
        statut=statut,
        type_installation=type_installation
    )


@installations_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Créer une nouvelle installation"""
    if request.method == 'POST':
        try:
            installation = Installation(
                etablissement_id=int(request.form.get('etablissement_id')),
                technicien_id=request.form.get('technicien_id', type=int),
                type_installation=request.form.get('type_installation'),
                statut=request.form.get('statut', 'EN_ATTENTE'),
                commentaire=request.form.get('commentaire')
            )
            
            date_installation = request.form.get('date_installation')
            if date_installation:
                installation.date_installation = datetime.strptime(date_installation, '%Y-%m-%dT%H:%M')
            
            db.session.add(installation)
            db.session.commit()
            
            flash(f'Installation créée avec succès', 'success')
            return redirect(url_for('installations.view', id=installation.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    etablissements = Etablissement.query.all()
    techniciens = User.query.filter_by(role='TECHNICIEN').all()
    
    return render_template(
        'installations/create.html',
        etablissements=etablissements,
        techniciens=techniciens
    )


@installations_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id):
    """Afficher les détails d'une installation"""
    installation = Installation.query.get_or_404(id)
    return render_template('installations/view.html', installation=installation)


@installations_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier une installation"""
    installation = Installation.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            installation.type_installation = request.form.get('type_installation')
            installation.statut = request.form.get('statut')
            installation.commentaire = request.form.get('commentaire')
            
            technicien_id = request.form.get('technicien_id')
            if technicien_id:
                installation.technicien_id = int(technicien_id)
            
            date_installation = request.form.get('date_installation')
            if date_installation:
                installation.date_installation = datetime.strptime(date_installation, '%Y-%m-%dT%H:%M')
            
            db.session.commit()
            flash(f'Installation modifiée avec succès', 'success')
            return redirect(url_for('installations.view', id=installation.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    techniciens = User.query.filter_by(role='TECHNICIEN').all()
    return render_template('installations/edit.html', installation=installation, techniciens=techniciens)


@installations_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer une installation"""
    installation = Installation.query.get_or_404(id)
    
    try:
        db.session.delete(installation)
        db.session.commit()
        flash(f'Installation supprimée avec succès', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('installations.index'))


@installations_bp.route('/api/stats', methods=['GET'])
@login_required
def stats():
    """API pour les statistiques des installations"""
    total = Installation.query.count()
    en_attente = Installation.query.filter_by(statut='EN_ATTENTE').count()
    en_cours = Installation.query.filter_by(statut='EN_COURS').count()
    terminees = Installation.query.filter_by(statut='TERMINEES').count()
    
    return jsonify({
        'total': total,
        'en_attente': en_attente,
        'en_cours': en_cours,
        'terminees': terminees
    })
