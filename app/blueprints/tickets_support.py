from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from datetime import datetime

from extensions import db
from models import TicketSupport, Etablissement, User

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')


@tickets_bp.route('/', methods=['GET'])
@login_required
def index():
    """Liste tous les tickets avec pagination et filtrage"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    statut = request.args.get('statut', '')
    priorite = request.args.get('priorite', '')
    categorie = request.args.get('categorie', '')
    
    query = TicketSupport.query
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                TicketSupport.titre.ilike(f'%{search}%'),
                TicketSupport.description.ilike(f'%{search}%')
            )
        )
    
    if statut:
        query = query.filter(TicketSupport.statut == statut)
    
    if priorite:
        query = query.filter(TicketSupport.priorite == priorite)
    
    if categorie:
        query = query.filter(TicketSupport.categorie == categorie)
    
    # Pagination
    pagination = query.order_by(desc(TicketSupport.date_creation)).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    tickets = pagination.items
    
    return render_template(
        'tickets/index.html',
        tickets=tickets,
        pagination=pagination,
        search=search,
        statut=statut,
        priorite=priorite,
        categorie=categorie
    )


@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Créer un nouveau ticket"""
    if request.method == 'POST':
        try:
            ticket = TicketSupport(
                etablissement_id=int(request.form.get('etablissement_id')),
                titre=request.form.get('titre'),
                description=request.form.get('description'),
                priorite=request.form.get('priorite', 'NORMALE'),
                categorie=request.form.get('categorie'),
                statut='OUVERT'
            )
            
            technicien_id = request.form.get('technicien_id')
            if technicien_id:
                ticket.technicien_id = int(technicien_id)
            
            db.session.add(ticket)
            db.session.commit()
            
            flash(f'Ticket créé avec succès (#{ ticket.id})', 'success')
            return redirect(url_for('tickets.view', id=ticket.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    etablissements = Etablissement.query.all()
    techniciens = User.query.filter_by(role='TECHNICIEN').all()
    
    return render_template(
        'tickets/create.html',
        etablissements=etablissements,
        techniciens=techniciens
    )


@tickets_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id):
    """Afficher les détails d'un ticket"""
    ticket = TicketSupport.query.get_or_404(id)
    return render_template('tickets/view.html', ticket=ticket)


@tickets_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier un ticket"""
    ticket = TicketSupport.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            ticket.titre = request.form.get('titre')
            ticket.description = request.form.get('description')
            ticket.priorite = request.form.get('priorite')
            ticket.statut = request.form.get('statut')
            ticket.categorie = request.form.get('categorie')
            
            technicien_id = request.form.get('technicien_id')
            if technicien_id:
                ticket.technicien_id = int(technicien_id)
            else:
                ticket.technicien_id = None
            
            # Marquer comme résolu
            if ticket.statut == 'RESOLU' and not ticket.date_resolution:
                ticket.date_resolution = datetime.utcnow()
            
            db.session.commit()
            flash(f'Ticket #{ticket.id} modifié avec succès', 'success')
            return redirect(url_for('tickets.view', id=ticket.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    techniciens = User.query.filter_by(role='TECHNICIEN').all()
    return render_template('tickets/edit.html', ticket=ticket, techniciens=techniciens)


@tickets_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer un ticket"""
    ticket = TicketSupport.query.get_or_404(id)
    ticket_id = ticket.id
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        flash(f'Ticket #{ticket_id} supprimé avec succès', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('tickets.index'))


@tickets_bp.route('/api/stats', methods=['GET'])
@login_required
def stats():
    """API pour les statistiques des tickets"""
    total = TicketSupport.query.count()
    ouverts = TicketSupport.query.filter_by(statut='OUVERT').count()
    en_cours = TicketSupport.query.filter_by(statut='EN_COURS').count()
    resolus = TicketSupport.query.filter_by(statut='RESOLU').count()
    
    # Priorités
    urgents = TicketSupport.query.filter_by(priorite='URGENTE').count()
    
    return jsonify({
        'total': total,
        'ouverts': ouverts,
        'en_cours': en_cours,
        'resolus': resolus,
        'urgents': urgents
    })
