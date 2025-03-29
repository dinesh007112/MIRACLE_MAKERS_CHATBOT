from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, FloatField, SelectMultipleField, RadioField, IntegerField
from wtforms.validators import DataRequired, NumberRange
import os
from exercise_dataset import EXERCISE_DATASET, GOAL_TIPS, AREA_MODIFICATIONS, TIPS, SAFETY_GUIDELINES
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Delete existing database file if it exists
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exercise.db')
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except:
        pass

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    disability = db.Column(db.String(100), nullable=False)
    fitness_level = db.Column(db.String(50), nullable=False)
    primary_goal = db.Column(db.String(50), nullable=False)
    uncomfortable_areas = db.Column(db.String(200))
    medical_conditions = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.name}>'

class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    height = FloatField('Height (cm)', validators=[DataRequired()])
    disability = SelectField('Disability', choices=[
        ('spinal_cord_injury', 'Spinal Cord Injury'),
        ('cerebral_palsy', 'Cerebral Palsy'),
        ('multiple_sclerosis', 'Multiple Sclerosis'),
        ('arthritis', 'Arthritis'),
        ('mobility_impairment', 'Mobility Impairment')
    ], validators=[DataRequired()])
    fitness_level = SelectField('Fitness Level', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], validators=[DataRequired()])
    primary_goal = RadioField('Primary Goal', choices=[
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain')
    ], validators=[DataRequired()])
    uncomfortable_areas = SelectMultipleField('Areas of Discomfort', choices=[
        ('back', 'Back'),
        ('knees', 'Knees'),
        ('shoulders', 'Shoulders'),
        ('neck', 'Neck'),
        ('hips', 'Hips'),
        ('wrist', 'Wrist'),
        ('ankles', 'Ankles'),
        ('none', 'None')
    ])
    submit = SubmitField('Get Recommendations')

def get_exercise_recommendations(user):
    weekly_schedule = {}
    contraindications = []
    tips = []
    
    # Get base recommendations from dataset
    if user.disability in EXERCISE_DATASET:
        disability_data = EXERCISE_DATASET[user.disability].get(user.fitness_level, {})
        goal_data = disability_data.get(user.primary_goal, {})
        weekly_schedule = goal_data.get('schedule', {})
        
        # Add disability-specific tips
        if user.disability in TIPS:
            tips.extend(TIPS[user.disability])
        
        # Add goal-specific tips
        if user.primary_goal in GOAL_TIPS:
            tips.extend(GOAL_TIPS[user.primary_goal])
        
        # Add safety guidelines
        if user.disability in SAFETY_GUIDELINES:
            contraindications.extend(SAFETY_GUIDELINES[user.disability])
    
    # Add modifications for uncomfortable areas
    uncomfortable_areas = user.uncomfortable_areas.split(',') if user.uncomfortable_areas else []
    for area in uncomfortable_areas:
        if area in AREA_MODIFICATIONS:
            contraindications.extend(AREA_MODIFICATIONS[area]['tips'])
            # Add modifications to each day's exercises
            for day in weekly_schedule:
                # Add 2-3 area-specific exercises to each day
                area_exercises = AREA_MODIFICATIONS[area]['exercises'][:3]
                weekly_schedule[day].extend(area_exercises)
    
    return weekly_schedule, contraindications, tips

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            age=form.age.data,
            weight=form.weight.data,
            height=form.height.data,
            disability=form.disability.data,
            fitness_level=form.fitness_level.data,
            uncomfortable_areas=','.join(form.uncomfortable_areas.data),
            primary_goal=form.primary_goal.data
        )
        db.session.add(user)
        db.session.commit()
        
        weekly_schedule, contraindications, tips = get_exercise_recommendations(user)
        return render_template('recommendations.html', user=user, weekly_schedule=weekly_schedule, contraindications=contraindications, tips=tips)
    
    return render_template('index.html', form=form)

@app.route('/recommendations/<int:user_id>')
def recommendations(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get exercise recommendations based on user's disability, fitness level, and goal
    disability_exercises = EXERCISE_DATASET.get(user.disability, {})
    fitness_level_exercises = disability_exercises.get(user.fitness_level, {})
    goal_exercises = fitness_level_exercises.get(user.primary_goal, {})
    weekly_schedule = goal_exercises.get('schedule', {})
    
    # Get tips and safety guidelines
    tips = GOAL_TIPS.get(user.primary_goal, [])
    safety_guidelines = []
    
    # Add modifications for uncomfortable areas
    uncomfortable_areas = user.uncomfortable_areas.split(',') if user.uncomfortable_areas else []
    for area in uncomfortable_areas:
        if area in AREA_MODIFICATIONS:
            safety_guidelines.extend(AREA_MODIFICATIONS[area]['tips'])
            # Add area-specific exercises to each day
            for day in weekly_schedule:
                area_exercises = AREA_MODIFICATIONS[area]['exercises']
                weekly_schedule[day].extend(area_exercises)
    
    return render_template('recommendations.html',
                         user=user,
                         weekly_schedule=weekly_schedule,
                         tips=tips,
                         safety_guidelines=safety_guidelines)

def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()  # Initialize database tables
    app.run(debug=True)