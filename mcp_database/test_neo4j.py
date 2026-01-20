from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
auth = ("neo4j", "password")

driver = GraphDatabase.driver(uri, auth=auth)

with driver.session() as session:
    result = session.run("RETURN 'Neo4j connected' AS msg")
    print(result.single()["msg"])

driver.close()
