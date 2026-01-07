from app import db
from datetime import datetime

class Scenario(db.Model):
    """Model for simulation scenarios."""
    __tablename__ = 'scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    simulation_period = db.Column(db.Integer, nullable=False)  # in months
    usage_pattern = db.Column(db.String(20), nullable=False)  # light, moderate, heavy
    maintenance_strategy = db.Column(db.String(20), nullable=False)  # reactive, preventive, predictive
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    equipment = db.relationship('Equipment', backref='scenarios')
    user = db.relationship('User', backref='scenarios')
    
    def __repr__(self):
        return f'<Scenario {self.name}>'
    
    def to_dict(self):
        """Convert scenario to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name if self.equipment else None,
            'simulation_period': self.simulation_period,
            'usage_pattern': self.usage_pattern,
            'maintenance_strategy': self.maintenance_strategy,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class SimulationResult(db.Model):
    """Model for storing simulation results."""
    __tablename__ = 'simulation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=False)
    result_data = db.Column(db.JSON, nullable=False)  # Store simulation results as JSON
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    scenario = db.relationship('Scenario', backref='results')
    
    def __repr__(self):
        return f'<SimulationResult for Scenario {self.scenario_id}>'
