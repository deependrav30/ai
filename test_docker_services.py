"""
Test Docker Services Connectivity
Tests Redis, PostgreSQL, and ChromaDB connections
"""
import sys

print("🔍 Testing Docker Services Connectivity\n")
print("="*60)

# Test 1: Redis
print("\n1️⃣  Testing Redis (Working Memory) - Port 6380")
try:
    import redis
    client = redis.Redis(host='localhost', port=6380, decode_responses=True, socket_connect_timeout=2)
    client.ping()
    client.set('test_key', 'test_value')
    value = client.get('test_key')
    client.delete('test_key')
    print(f"   ✅ Redis: Connected and operational")
    print(f"   📊 Version: {client.info('server')['redis_version']}")
except Exception as e:
    print(f"   ❌ Redis: Failed - {e}")
    sys.exit(1)

# Test 2: PostgreSQL
print("\n2️⃣  Testing PostgreSQL (Episodic Memory) - Port 5433")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='episodic_memory',
        user='ai_agent',
        password='ai_agent_password',
        connect_timeout=2
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM past_tickets;')
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"   ✅ PostgreSQL: Connected and operational")
    print(f"   📊 Version: {version.split(',')[0]}")
    print(f"   📋 Past tickets in DB: {count}")
except Exception as e:
    print(f"   ❌ PostgreSQL: Failed - {e}")
    sys.exit(1)

# Test 3: ChromaDB
print("\n3️⃣  Testing ChromaDB (Semantic Memory) - Port 8001")
try:
    import chromadb
    from chromadb.config import Settings
    
    client = chromadb.HttpClient(
        host='localhost',
        port=8001,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Test collection operations
    collection = client.get_or_create_collection("test_memory")
    collection.add(
        ids=["test1"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"test": "connectivity"}]
    )
    count = collection.count()
    client.delete_collection("test_memory")
    
    print(f"   ✅ ChromaDB: Connected and operational")
    print(f"   📊 Test collection operations: Success")
    print(f"   📋 Active collections: {len(client.list_collections())}")
except Exception as e:
    print(f"   ❌ ChromaDB: Failed - {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ All Docker services are healthy and operational!")
print("\n📋 Service Summary:")
print("  • Redis (6380): Working memory - ephemeral task context")
print("  • PostgreSQL (5433): Episodic memory - past tickets & resolutions")
print("  • ChromaDB (8001): Semantic memory - document embeddings")
print("\n✨ Memory agents are ready to use distributed storage!")
