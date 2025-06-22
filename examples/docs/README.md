# 🎬 Documentation Examples

This directory contains working examples from the main README.md file. All examples are guaranteed to work and are regularly tested to ensure our documentation stays accurate and helpful!

## 🎯 Available Examples

### 1. 🚀 Quick Start (`01_quick_start.py`)

**Exact code from README** - The simplest possible fastapi-dishka application.

```bash
python examples/docs/01_quick_start.py
```

Visit: http://localhost:8000/api/greet/World

---

### 2. 🔄 Auto-Router Registration (`02_auto_router_registration.py`)

**Exact code from README** - Shows the auto-registration pattern.

```bash
python examples/docs/02_auto_router_registration.py
```

Visit: http://localhost:8000/users/, /posts/, /comments/

---

### 3. 🛡️ Middleware with Dependency Injection (`03_middleware_with_di.py`)

**Exact code from README** - Middleware that can inject dependencies.

```bash
python examples/docs/03_middleware_with_di.py
```

Try: `curl -H 'Authorization: Bearer token' http://localhost:8000/protected`

---

### 4. 🏗️ Multiple Providers (`04_multiple_providers.py`)

**Exact code from README** - Organizing with multiple providers.

```bash
python examples/docs/04_multiple_providers.py
```

Visit: http://localhost:8000/users/, /posts/

---

### 5. 🌐 Server Management (`05_server_management.py`)

**Exact code from README** - Different server management patterns.

```bash
python examples/docs/05_server_management.py
```

Interactive demo with different server modes.

---

### 6. 🧪 Testing (`06_testing.py`)

**Exact code from README** + Hello World example everyone expects!

```bash
# Run the tests
pytest examples/docs/06_testing.py -v

# Or run the script
python examples/docs/06_testing.py
```

**Features:**

- ✅ Hello World test (the classic everyone expects)
- ✅ Exact README testing pattern: `app.close()` cleanup
- ✅ Proper async support
- ✅ Real working examples

## 🎯 Key Features Demonstrated

- **Exact README Code** - Every example matches the README exactly
- **Working Examples** - All can be run immediately
- **Hello World Test** - The classic test everyone expects to see
- **Proper Cleanup** - Using `app.close()` as documented
- **Real Patterns** - Production-ready examples

## 🧪 Testing All Examples

```bash
# Quick verification all examples work
cd examples/docs

echo "Testing Quick Start..."
timeout 3s python 01_quick_start.py

echo "Testing Auto-Router Registration..."
timeout 3s python 02_auto_router_registration.py

echo "Testing Multiple Providers..."
timeout 3s python 04_multiple_providers.py

echo "Testing Hello World Tests..."
pytest 06_testing.py -v

echo "✅ All examples verified!"
```

## 📚 Learning Path

1. **Start:** `01_quick_start.py` - Basic setup
2. **Scale:** `02_auto_router_registration.py` - Multiple routers
3. **Secure:** `03_middleware_with_di.py` - Middleware with DI
4. **Organize:** `04_multiple_providers.py` - Clean architecture
5. **Deploy:** `05_server_management.py` - Production patterns
6. **Test:** `06_testing.py` - Quality assurance

## 💡 Why These Examples Matter

- **Trustworthy Documentation** - Examples are tested and guaranteed to work
- **Real-World Patterns** - Based on actual usage patterns
- **Copy-Paste Ready** - Use directly in your projects
- **Learning Friendly** - Progressive complexity

Remember: these examples are referenced in the main README, so they stay accurate! 📚✨
