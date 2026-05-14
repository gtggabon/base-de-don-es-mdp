from flask import Blueprint

# Import all blueprints
from .contrats import contrats_bp
from .etablissements import etablissements_bp
from .installations import installations_bp
from .tickets_support import tickets_bp

__all__ = ['contrats_bp', 'etablissements_bp', 'installations_bp', 'tickets_bp']
