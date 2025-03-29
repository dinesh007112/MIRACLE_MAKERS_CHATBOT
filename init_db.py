from app import app, db
import os

def initialize_database():
    # Get the database file path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exercise.db')
    
    try:
        # Remove existing database if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        
        # Create database tables
        with app.app_context():
            db.create_all()
            print("Successfully created new database tables!")
            
            # Verify tables were created
            tables = db.engine.table_names()
            print("\nCreated tables:")
            for table in tables:
                print(f"- {table}")
                
            print("\nDatabase initialization complete!")
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_database() 