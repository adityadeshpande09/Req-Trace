"""
Simple test script to add nodes directly to Neo4j
Run from backend directory with venv activated
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env')

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

print("=" * 60)
print("ReqTrace Simple Graph Test")
print("=" * 60)
print()

# Connect to Neo4j
print(f"Connecting to Neo4j at {NEO4J_URI}...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

try:
    # Test connection
    driver.verify_connectivity()
    print("✓ Connected to Neo4j successfully!")
    print()
    
    with driver.session() as session:
        # Clear existing data (optional)
        print("Clearing existing test data...")
        session.run("MATCH (n) WHERE n.test = true DELETE n")
        print("✓ Cleared")
        print()
        
        # Create sample nodes
        print("Creating sample requirement nodes...")
        
        # Requirement 1
        session.run("""
            CREATE (r:Requirement {
                name: 'User Authentication',
                description: 'System shall allow users to authenticate with username and password',
                priority: 'High',
                test: true
            })
        """)
        
        # Requirement 2
        session.run("""
            CREATE (r:Requirement {
                name: 'Two-Factor Authentication',
                description: 'System shall support two-factor authentication',
                priority: 'High',
                test: true
            })
        """)
        
        # Feature
        session.run("""
            CREATE (f:Feature {
                name: 'Login Feature',
                description: 'User login and authentication feature',
                status: 'Planned',
                test: true
            })
        """)
        
        # Stakeholder
        session.run("""
            CREATE (s:Stakeholder {
                name: 'John Smith',
                role: 'Security Team Lead',
                department: 'Security',
                test: true
            })
        """)
        
        # Stakeholder 2
        session.run("""
            CREATE (s:Stakeholder {
                name: 'Sarah Johnson',
                role: 'Product Manager',
                department: 'Product',
                test: true
            })
        """)
        
        # Constraint
        session.run("""
            CREATE (c:Constraint {
                name: 'Q1 Release Deadline',
                description: 'Feature must be ready for Q1 release',
                type: 'Timeline',
                test: true
            })
        """)
        
        # Team
        session.run("""
            CREATE (t:Team {
                name: 'Security Team',
                department: 'Security',
                test: true
            })
        """)
        
        print("✓ Created 7 nodes")
        print()
        
        # Create relationships
        print("Creating relationships...")
        
        session.run("""
            MATCH (f:Feature {name: 'Login Feature', test: true})
            MATCH (r:Requirement {name: 'User Authentication', test: true})
            CREATE (f)-[:IMPLEMENTS]->(r)
        """)
        
        session.run("""
            MATCH (f:Feature {name: 'Login Feature', test: true})
            MATCH (r:Requirement {name: 'Two-Factor Authentication', test: true})
            CREATE (f)-[:IMPLEMENTS]->(r)
        """)
        
        session.run("""
            MATCH (s:Stakeholder {name: 'John Smith', test: true})
            MATCH (r:Requirement {name: 'Two-Factor Authentication', test: true})
            CREATE (s)-[:REQUESTED]->(r)
        """)
        
        session.run("""
            MATCH (s:Stakeholder {name: 'Sarah Johnson', test: true})
            MATCH (c:Constraint {name: 'Q1 Release Deadline', test: true})
            CREATE (s)-[:DEFINED]->(c)
        """)
        
        session.run("""
            MATCH (s:Stakeholder {name: 'John Smith', test: true})
            MATCH (t:Team {name: 'Security Team', test: true})
            CREATE (s)-[:MEMBER_OF]->(t)
        """)
        
        print("✓ Created 5 relationships")
        print()
        
        # Count nodes
        result = session.run("MATCH (n {test: true}) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"✓ Total test nodes in database: {count}")
        print()
        
    print("=" * 60)
    print("SUCCESS! Test graph created!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Go to http://localhost:5173 and refresh")
    print("2. You should see nodes in the Knowledge Graph!")
    print()
    print("Or view in Neo4j Browser:")
    print("1. Go to http://localhost:7474")
    print("2. Run: MATCH (n {test: true}) RETURN n")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.close()
    print("Connection closed.")