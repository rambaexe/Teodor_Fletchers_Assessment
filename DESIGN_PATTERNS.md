# Design patterns

## Used in this project

| Pattern | Where | Why |
|---|---|---|
| Interface (ABC) | `DocumentExtractor`, `OcrProvider`, `Enricher` | Code depends on contracts, not on PDF / Word / a vendor |
| Polymorphism | `service.py`: `extractor.extract()` | No `if pdf / elif docx` anywhere |
| Factory + registry | `extractor/factory.py` | New format = new class + one `register()` line |
| Chain of Responsibility | `ExtractorFactory.for_file()` asks each `can_handle()` | Type detected from file content, not extension |
| Strategy | OCR / enricher implementations; PDF page: text layer vs OCR | Swap mock -> real vendor without touching callers |
| Dependency Injection | constructors + FastAPI `Depends` | Classes receive what they need; easy to swap / test |
| Composition Root | `api/dependencies.py` | One place where concrete classes are chosen |
| Facade / Service layer | `IngestionService.process()` | Routes make one call; the pipeline is hidden behind it |
| Repository | `db/repository.py` | No SQL outside `db/`; Postgres = change URL |
| Adapter | PDF / DOCX extractors wrap `pypdf` / `python-docx` | Third-party libraries isolated to one file each |
| Observer (callback) | `on_progress` | Extractors report progress without knowing about the DB |
| DTO | `ExtractionResult`, `Enrichment`, `api/schemas.py` | One output shape for every format; API separate from DB |

**Deliberately not used:** Decorator (e.g. `FallbackEnricher`, `CachingEnricher`): most useful with a real LLM. Template Method: PDF and Word differ too much. Repository interface: only one implementation (YAGNI).

## SOLID in this project

| Principle | How |
|---|---|
| **S** Single responsibility | routes = HTTP, extractors = parsing, enricher = enrichment, repository = storage, service = orchestration |
| **O** Open/closed | new format = new extractor class; nothing existing edited |
| **L** Liskov substitution | every extractor returns `ExtractionResult`, every enricher `Enrichment`; any can replace another |
| **I** Interface segregation | small interfaces: `can_handle` + `extract`, `extract_text`, `enrich` |
| **D** Dependency inversion | service depends on interfaces; concrete classes only in `dependencies.py` |

---

# Guide: check your knowledge

Each concept: what it is in plain words, a real-life picture, a tiny example, then a question. Try answering before opening the answer.

## 4 pillars of OOP

### 1. Encapsulation
**Plain words:** keep data and the code that changes it together; hide the inside.
**Real life:** a TV remote. You press buttons; you never touch the circuit board.
```python
class BankAccount:
    def __init__(self):
        self._balance = 0          # hidden: don't touch directly

    def deposit(self, amount):     # the only way in
        if amount > 0:
            self._balance += amount
```
<details><summary>Check: why not let people set <code>_balance</code> directly?</summary>

Then anyone could set a negative balance. Going through `deposit()` lets the class enforce its rules.
</details>

### 2. Abstraction
**Plain words:** show *what* something does, hide *how*.
**Real life:** driving a car. You use the pedal; you don't need to know how the engine works.
```python
ocr.extract_text(image)   # mock or AWS? the caller doesn't know or care
```
<details><summary>Check: what's the difference between abstraction and encapsulation?</summary>

Abstraction = hiding *complexity* (a simple surface). Encapsulation = hiding *data* (protecting the inside). They usually go together.
</details>

### 3. Inheritance
**Plain words:** a class gets everything from a parent class and can add or change things.
**Real life:** a "car" is a kind of "vehicle": it has wheels like every vehicle, plus its own things.
```python
class Animal:
    def breathe(self): return "breathing"

class Dog(Animal):          # gets breathe() for free
    def speak(self): return "woof"
```
<details><summary>Check: when should you NOT use inheritance?</summary>

When it's not a true "is a" relationship. A `Car` *has an* `Engine`; it isn't one. Use composition (pass objects in) instead.
</details>

### 4. Polymorphism
**Plain words:** same call, different behaviour depending on the object.
**Real life:** "play" on a guitar vs a piano: same instruction, different sound.
```python
for animal in [Dog(), Cat()]:
    animal.speak()          # "woof", then "meow"
```
<details><summary>Check: where is polymorphism in this project?</summary>

`extractor.extract(path)` in `service.py`: it runs PDF or Word logic without the service checking which.
</details>

## SOLID

### S: Single responsibility
**Plain words:** a class should do one job.
**Real life:** a chef cooks, a waiter serves. One person doing both does both badly.
```python
# bad: one Report class that calculates, prints AND emails
# good: Calculator, Printer, Emailer, each with one job
```
<details><summary>Check: in this project, why are routes and the service separate?</summary>

Routes only deal with HTTP; the service only runs the pipeline. A change to one doesn't touch the other.
</details>

### O: Open/closed
**Plain words:** add new behaviour by adding code, not by editing old code.
**Real life:** a power strip. You plug in a new device; you don't rewire the strip.
```python
# bad: every new shape = edit this function
if shape == "circle": ...
elif shape == "square": ...
# good: each shape has its own area(); add a class for a new shape
```
<details><summary>Check: how do you add .txt support in this project?</summary>

Write a `TxtExtractor` class and add one `register()` line. No existing code changes.
</details>

### L: Liskov substitution
**Plain words:** a child class must work anywhere its parent works.
**Real life:** a rental company promises "a car". Any car they give you must drive.
```python
def total(shapes): return sum(s.area() for s in shapes)
# works for Circle, Square... any Shape. A subclass whose area() crashed would break the rule.
```
<details><summary>Check: classic example of breaking it?</summary>

`Square(Rectangle)`: setting the width of a square also changes its height, which surprises code that expects a rectangle.
</details>

### I: Interface segregation
**Plain words:** many small interfaces beat one big one.
**Real life:** a TV remote with 5 buttons you use vs 80 you don't.
```python
# bad: Worker has work() + eat(), so a Robot must fake eat()
# good: Workable.work() and Eatable.eat() separately
```
<details><summary>Check: what's the risk of a big interface?</summary>

Classes must implement methods they don't need (empty or fake ones), which is confusing and fragile.
</details>

### D: Dependency inversion
**Plain words:** depend on a general idea, not a specific product.
**Real life:** a wall socket. Any plug fits; the wall isn't wired to one specific lamp.
```python
# bad
class Service:
    def __init__(self): self.db = MySQL()           # stuck with MySQL
# good
class Service:
    def __init__(self, db: Database): self.db = db  # any database
```
<details><summary>Check: what does this make easy?</summary>

Swapping implementations (MySQL to Postgres, real to mock) and testing with fakes.
</details>

## Common design patterns

### Creational: making objects

**Factory**: one place decides which object to create.
*Real life:* a restaurant kitchen. You order "pasta"; the kitchen decides how to make it.
```python
def make_shape(name): return Circle() if name == "circle" else Square()
```
<details><summary>Check: why not just call <code>Circle()</code> directly?</summary>

Callers would have to know every class. With a factory, adding a shape changes one place.
</details>

**Builder**: build a complex object step by step.
*Real life:* ordering a sandwich: bread, then filling, then sauce.
```python
Sandwich().bread("white").filling("ham").sauce("mayo").build()
```
<details><summary>Check: when is it useful?</summary>

When an object has many optional parts; it beats a constructor with 10 arguments.
</details>

**Singleton**: only one instance ever exists.
*Real life:* a country has one president at a time.
```python
config = Config()   # everyone uses this same object
```
<details><summary>Check: downside?</summary>

It's global state: hidden dependencies, harder to test. Often dependency injection is better.
</details>

### Structural: fitting objects together

**Adapter**: make something incompatible fit.
*Real life:* a UK-to-EU plug adapter.
```python
class PdfExtractor:            # wraps pypdf so it returns OUR format
    def extract(self, path): return to_our_format(pypdf.read(path))
```
<details><summary>Check: where in this project?</summary>

The PDF and Word extractors adapt `pypdf` and `python-docx` into `ExtractionResult`.
</details>

**Decorator**: wrap an object to add something, same interface.
*Real life:* putting a case on a phone. It's still a phone, now with protection.
```python
ocr = CachingOcr(RealOcr())    # same .read(), now with a cache
```
<details><summary>Check: difference from inheritance?</summary>

Decorators are added at runtime and can be stacked (`Logging(Caching(RealOcr()))`) without creating a subclass for every combination.
</details>

**Facade**: one simple front door to something complicated.
*Real life:* a hotel reception desk. One person sorts out rooms, taxis and dinner.
```python
service.process(doc_id)        # hides factory, extractor, OCR, enricher, DB
```
<details><summary>Check: where in this project?</summary>

`IngestionService.process()`: routes call one method instead of coordinating everything.
</details>

**Proxy**: a stand-in that controls access to the real thing.
*Real life:* a bank card stands in for your money, and checks your PIN first.
```python
class LazyImage:               # only loads the big file when first shown
    def show(self):
        self.real = self.real or load_image()
        self.real.show()
```
<details><summary>Check: Proxy vs Decorator?</summary>

They look similar. A proxy *controls access* (lazy loading, permissions); a decorator *adds features*.
</details>

**Composite**: treat a group the same as a single item.
*Real life:* a folder and a file both have a "size".
```python
folder.size()   # = sum of its files' and subfolders' sizes
```
<details><summary>Check: what problem does it solve?</summary>

Code can handle trees (folders, menus, UI components) without checking "is this one item or many?".
</details>

### Behavioural: how objects work together

**Strategy**: swappable ways of doing the same job.
*Real life:* getting to work by bike, bus or car. Same goal, different method.
```python
navigator = Navigator(route=BikeRoute())   # or BusRoute()
```
<details><summary>Check: where in this project?</summary>

`MockOcrProvider` vs a real OCR service; `MockLlmEnricher` vs a real LLM.
</details>

**Observer**: subscribers get notified when something happens.
*Real life:* subscribing to a YouTube channel. You're notified on each new video.
```python
button.on_click(save)      # save() runs whenever the button is clicked
```
<details><summary>Check: where in this project?</summary>

`on_progress`: the extractor reports progress and the service listens and stores it.
</details>

**Chain of Responsibility**: pass a request along until someone handles it.
*Real life:* customer support: level 1, then level 2, then a manager.
```python
for handler in handlers:
    if handler.can_handle(request):
        return handler
```
<details><summary>Check: where in this project?</summary>

`ExtractorFactory.for_file()` asks each extractor `can_handle()` in turn.
</details>

**Command**: turn an action into an object.
*Real life:* a waiter's order slip. It can be queued, passed on or cancelled.
```python
cmd = DeleteCommand(file)
cmd.execute()
cmd.undo()
```
<details><summary>Check: what does it enable?</summary>

Undo/redo, queues, scheduling and logging of actions.
</details>

**Template Method**: the parent fixes the steps; children fill in some of them.
*Real life:* a recipe. "Prepare, cook, serve" is fixed; *what* you cook changes.
```python
class Report:
    def make(self):                # fixed order
        self.header(); self.body(); self.footer()

class SalesReport(Report):
    def body(self): ...            # only this differs
```
<details><summary>Check: why isn't it used in this project?</summary>

PDF and Word extraction share too few steps, so forcing a common template would make the code worse.
</details>

**State**: behaviour changes depending on the current state.
*Real life:* a traffic light. What "next" does depends on whether it's red, amber or green.
```python
# document: queued -> processing -> done / failed; each state allows different actions
```
<details><summary>Check: where could it apply here?</summary>

Document status. Today it's a simple enum; a State pattern would help if each status had lots of different rules.
</details>

**Iterator**: go through items one by one without knowing how they're stored.
*Real life:* a playlist's "next song" button.
```python
for chunk in document.chunks:
    print(chunk.text)
```
<details><summary>Check: where do you use it every day in Python?</summary>

Every `for` loop: lists, dicts, files and generators are all iterators.
</details>
