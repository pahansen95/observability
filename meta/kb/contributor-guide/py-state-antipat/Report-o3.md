Python Anti-Patterns in State and Configuration Management

Executive Summary

Key Findings: In Python projects, seemingly “simple” patterns like module-level state, singletons, and implicit configuration can introduce hidden complexity and technical debt. Mature frameworks avoid these by keeping state explicit and injectable, minimizing global side effects, and making configuration data-driven rather than hard-coded. This leads to more testable, maintainable code. For example, passing dependencies (like database connections or API clients) into functions and classes, instead of fetching them from module globals, reduces hidden coupling and makes unit tests independent ￼ ￼. As the Zen of Python states, “Explicit is better than implicit” ￼ – a mantra that guides the recommended patterns.

Decision Matrix: When choosing an approach for state or config management, consider the context:
	•	Library Code: Avoid any reliance on global application state (e.g. Django settings or environment variables) inside the library. Instead, accept config values or objects as parameters or provide a helper to initialize the library with a config object. This ensures the library is usable in any environment and easily testable.
	•	Application Code: A single-process application can use a singletons or module-level objects only for truly shared, immutable configuration (such as constants). Mutable state and I/O should be confined to application startup or passed through context. Use an application factory or initialization function to build the app with its configuration, rather than initializing at import time ￼.
	•	Testing vs Production: If a pattern makes it hard to override components for tests (e.g. a hard-coded singleton that always connects to a real service), that pattern is a red flag. Prefer dependency injection, where test doubles (mocks, fakes) can be provided in place of real services. Testing ease is a strong indicator of good architecture.

Why It Matters: Global state and implicit configs can lead to unpredictable behavior, especially as projects grow or run in parallel. Hidden state creates coupling between distant parts of the code, causing tests or components to interfere with each other ￼ ￼. By contrast, explicit patterns (passing in config and dependencies) incur minor upfront complexity but save significant effort in debugging, scaling, and modifying the system later ￼. The recommendations in this report favor explicitness, clarity of data flow, and isolation of state, aligning with Python’s best practices and successful real-world projects.

Anti-Pattern Analysis

In this section, we analyze common anti-patterns in state management and configuration. Each of these approaches appears simple (often requiring less code or thought initially) but creates hidden complexities that violate clean architecture principles. We detail why each anti-pattern is attractive, the problems it introduces, and examples of real issues that arise, along with the cost of later refactoring.

1. Module-Level Mutable State and Singletons
	•	What it is: Defining module globals or using the Singleton pattern to hold state or configuration that many parts of the program use. For example, a module might create a database connection or client object at import time and other modules simply import and use it. In web frameworks, this often takes the form of a single settings object or a singleton App instance accessed globally.
	•	Why it seems attractive: It’s straightforward – any code that needs the resource can import the module and use the globally defined object. This avoids threading config through multiple function calls. Singleton patterns also ensure only one instance exists, simplifying resource sharing (e.g., “one database connection shared by all code”). To developers, it feels convenient to “set and forget” some config or object in one place and have it available everywhere.
	•	Hidden complexity: Global mutable state couples distant parts of the codebase. If any part of the code modifies the global, it affects all others unpredictably ￼ ￼. For instance, if a global config dict is changed in one module during a test, another test in a different module could inadvertently see the modified value, leading to order-dependent failures. This makes tests flaky and non-isolated ￼ ￼. Race conditions can occur in concurrent scenarios since global state is shared by threads (or asyncio tasks) without clear ownership ￼. Singletons that manage substantial state (like connection pools or caches) can leak across test cases or contexts – once initialized, you cannot easily create a second with different settings, which limits flexibility.
	•	Examples of problems:
	•	Test Interference: Environment variables in Python are exposed via a global dict os.environ. Code that reads os.environ deep inside functions is effectively using a global config. A test that temporarily sets os.environ['PATH'] for one function can unintentionally affect another test running concurrently or subsequently, which also relies on PATH ￼ ￼. Unless every test meticulously cleans up or you run tests serially, global state changes propagate and cause flickering tests.
	•	Inability to have multiple configurations: Singleton objects mean you cannot, for example, easily connect to two databases at once by instantiating two “DB connection” objects – the singleton enforces a single resource. If requirements change (say, a need to connect to multiple data sources, or to spawn two instances of an app with different settings), the singleton becomes a liability. Celery, the task queue library, faced this and undertook a major refactor called “The Big Instance” to remove its global app object specifically so multiple Celery apps can coexist in one process ￼.
	•	Hidden dependencies: A function may use a global without it being obvious in its signature. Developers reading or using that function might not realize it relies on some global config or object. This “action at a distance” violates the principle of least surprise. It also makes reuse difficult – pulling that function into a new context drags along the implicit requirement that some global must be set up.
	•	Lifecycle and order issues: If module A’s global depends on module B’s global (for example, two singletons that should be initialized in order), import order can become significant. Python’s import system doesn’t guarantee an order across modules except through dependencies, which can lead to subtle bugs if not managed carefully.
	•	Cost of fixing later: Refactoring global state out is painful. Code using global singletons tends to sprinkle access to them everywhere (e.g. many functions doing from app import settings or using a global logger). Removing it means changing function signatures to accept dependencies, updating countless call sites, and ensuring all parts receive the needed object. If an object was assumed to be one-per-process, making it multi-instance might break assumptions (e.g. cached singletons might assume only one initialization ever happens). The Celery team’s need to remain backward compatible required introducing a fallback to a default global app and even a debug mode to catch code implicitly using it ￼ ￼ – illustrating the complexity of untangling global state in a mature project.
	•	Evidence: Python experts warn that “mutable global objects can wind up coupling distant code” ￼ ￼. The problems are well known: tests interfering if they mutate globals, difficulty in reasoning about state, and inability to run components in isolation ￼ ￼. Tools like linters even flag uses of global keywords because they’re a common source of bugs ￼ ￼. In short, the convenience of a single reachable state is outweighed by the loss of clarity and safety.

2. Import-Time Side Effects and Implicit Initialization
	•	What it is: Performing non-trivial work at module import time – especially I/O or configuration loading – or having deep modules auto-import lots of sub-dependencies. A related anti-pattern is function-level dynamic imports solely to hide dependencies: e.g., importing a heavy library inside a function so the module’s top doesn’t reveal that dependency. These patterns obscure what the code actually requires and does, by pushing it into import or runtime side effects.
	•	Why it seems attractive: It can make the top-level code (and application startup code) very minimal. For example, a library might automatically read a config file or environment variables when imported, so the user doesn’t have to call a setup function. Function-level imports are sometimes used to reduce initial load time (import only when needed) or to avoid circular import problems by deferring an import. Both give a superficial impression of simplicity: you just import X and it’s ready to go, or you call a function and magically it imports what it needs on the fly.
	•	Hidden complexity: Import-time work violates “import should be idempotent and quick.” If importing a module reads files, contacts networks, or initializes hardware, then any script or test that imports it will incur that side effect and potential failure ￼ ￼. For example, if a library tries to read /etc/hosts at import, any environment missing that file (embedded system, container, CI) will error out during import, possibly crashing programs that weren’t even going to use that functionality ￼ ￼. It also slows down startup – import should ideally just load definitions, not execute long computations. With dynamic imports inside functions, the hidden dependency can lead to unexpected ImportErrors at runtime if the environment is missing something, and it’s not clear at module load that the dependency exists. It also complicates tooling (linters or bundlers might not detect the dependency).
	•	Examples of problems:
	•	Import-time config loading: A real example from a Django context: a third-party app’s module, on import, did from django.conf import settings and copied some values into its own app_settings at module level ￼. This means as soon as you import any part of that app, it snapshots the Django settings. In tests, using Django’s override_settings failed because the package had already cached the old value. The developer was forced to import the app’s settings module and manually tweak it as a workaround ￼. The recommended fix was to move that config access inside a function or property – i.e., evaluate it when needed, not at import ￼.
	•	Importing “the world”: The “import the world” anti-pattern refers to modules that at import time pull in a large number of other modules or do heavy initialization ￼ ￼. For instance, the Conda CLI was found to import 328 additional modules just by importing one subcommand module, doing things like parsing YAML and loading config files before the program’s main logic even ran ￼ ￼. This led to a slow startup and high memory usage, even if the user’s command didn’t need most of those imports ￼. In testing, this is exacerbated when tests import many modules – each test might trigger loads of unused code, slowing the suite significantly ￼.
	•	Runtime dynamic import pitfalls: While local imports can be useful (e.g., to reduce startup time or break circular dependencies), overusing them to hide design problems is dangerous. If a function does import X internally because X is a heavy dependency, any error in importing X will only show up when that function is called, potentially late in execution or in a less controlled context. It also means static analysis or grepping for X might not reveal that dependency, making the code harder to understand. In some cases, developers forget the import is hidden and call the function assuming the module was imported elsewhere.
	•	Cost of fixing later: If import-time side effects are pervasive, unraveling them means auditing every module for hidden logic. This can break backward compatibility (e.g., if users expected import mylib to auto-load config, they’ll now have to call an init function). Lazy imports sprinkled in functions might need to be hoisted to module top if they are truly required, which could re-introduce those startup costs unless a better structure (like plugins or optional submodules) is adopted. Essentially, one may need to redesign initialization: e.g., provide an explicit initialize(config) API that loads what’s needed, instead of doing it on import. This can be a far-reaching change if the original design assumed implicit initialization everywhere.
	•	Evidence: Import-time I/O and side effects are strongly discouraged in the community. Brandon Rhodes notes that errors at import time are “far more serious than errors at runtime” because they bypass normal error handling and can bring down the app before it even starts ￼. He also points out that code may be imported and never used – doing expensive work in that case is pure overhead on programs that didn’t need it ￼. The principle that “Importing code should be mostly free of side effects” ￼ ￼ is widely accepted. Tools and practices exist (like using entry-point functions or application factories) to defer heavy lifting until the program explicitly calls for it.

3. Implicit Configuration via Environment or Global Context
	•	What it is: Relying on ambient environment or context to configure the application, without explicitly passing configuration through. This includes reading environment variables deep in the code (e.g., os.getenv("API_TOKEN") scattered in different modules), or assuming a framework’s global configuration object is present (like using django.conf.settings directly inside library code, or Flask’s current_app proxy anywhere in the codebase).
	•	Why it seems attractive: It’s quick and easy. The developer doesn’t have to plumb configuration values through multiple layers; any function can call os.getenv or refer to a global settings object. This also mirrors how some frameworks work – Django, for example, encourages using a settings module that is essentially a singleton for config. New developers often imitate this in their own code, because it reduces the need to pass around a config object or parameters. It also centralizes configuration in one place (the environment or a settings file), which feels convenient.
	•	Hidden complexity: Strong coupling to external environment. If parts of your code call os.getenv("X") at will, the behavior of your code now depends on external state that isn’t visible in the function signature or parameters. This makes testing harder – to test function foo() that does os.getenv("X"), you must manipulate environment variables outside of the function, which is a side effect. It’s easy to forget to reset an env var and pollute other tests. Also, environment configuration tends to be global process-wide, so you can’t easily run two instances of your app with different configs in the same process (useful for certain integration tests or multi-tenant scenarios). In libraries, assuming a certain global config (like Django settings) means the library only works within that context. If someone tries to use the library outside of Django, it breaks or behaves inconsistently.
	•	Examples of problems:
	•	Third-party library config assumptions: A Django package might use from django.conf import settings internally to get a setting value. If used in a Django project, fine – but if someone wants to use that package’s functionality outside of Django (or before Django setup), it fails. Even within Django, if the package imports settings at module load, it captures the config too early (as seen in the earlier example) or doesn’t notice changes at runtime ￼ ￼.
	•	Direct environment use scattered in code: Imagine an application that uses os.getenv("REGION") in various modules to toggle behavior. To run a test with a non-default region, every test needs to set REGION before importing those modules – and if two tests expect different regions, they cannot run in the same process concurrently. Moreover, if a developer wants to run two instances of an app (with different regions) in threads or async tasks, they can’t, because os.environ is process-wide. The 12-Factor App methodology recommends storing config in the environment, but importantly it also recommends reading it once at startup and then injecting it into the app, not reading it everywhere on the fly. Failing to do so yields highly implicit behavior.
	•	Framework context misuse: Flask provides flask.current_app and flask.g (request-local storage) as global proxies. In a web request context, these are fine to avoid threading parameters through every function. But if that pattern bleeds into business logic, you end up with functions that only work when a Flask app context is active (they’ll throw errors if used outside a request). For instance, calling a function that uses current_app.config["X"] will fail unless an application context is pushed. This couples what could be generic logic to the web framework’s global state.
	•	Cost of fixing later: Reversing implicit config usage means surfacing configuration through explicit interfaces. This can be a big refactor: every place that assumed settings.FOO or os.getenv("FOO") needs to accept a parameter or be handed a config object. This often cascades upwards – you might end up changing the signature of core functions or class constructors to take a config, then adjusting everywhere those are called. If not done uniformly, you risk a mix of patterns that’s even more confusing (some functions use passed config, others still reach out to global). It’s best to establish a clear policy early: e.g., “All config access happens in the config.py module and nowhere else; that module reads env vars and constructs a Config object that gets passed in.” Retrofitting that policy later touches many files and requires extensive testing to ensure no behavior changed.
	•	Evidence: The drawbacks of implicit config are often discussed in the context of testing and flexibility. The Zen of Python’s emphasis on explicitness rings true here ￼. We see that frameworks like Flask moved to an application factory pattern: instead of a global app, they recommend a function create_app(config) to configure and return a new app instance ￼. This allows different configs for testing vs production (by passing in test_config) and avoids “tricky issues as the project grows” that stem from a global app object ￼. Similarly, FastAPI encourages dependency injection and explicit Pydantic config objects, rather than relying on globals. These successful projects demonstrate that even though global config can work (Django does it), the trend is toward explicit, per-instance configuration for better modularity.

Having identified these anti-patterns, we now turn to the practices and patterns that should be used. The next section outlines recommended approaches for dependency injection, configuration management, and state handling that address the issues above.

Recommended Patterns

Each of these recommended patterns is designed to replace a corresponding anti-pattern with a more robust solution. The overarching theme is controlled, explicit flow of dependencies and configuration. Instead of hiding complexity in globals or import side effects, these patterns make the code’s requirements clear. They may introduce a bit more verbosity or upfront wiring, but the payoff is easier testing, clearer reasoning, and better adaptability to change.

1. Explicit Dependency Injection

What & Why: Dependency Injection (DI) means giving an object or function the things it needs, rather than having it fetch them itself. In Python, we typically implement DI in a lightweight way: by passing arguments to functions or constructors (also known as constructor injection in OOP) ￼. This contrasts with frameworks in other languages (Java Spring, etc.) that use containers – in Python, simple is better: just pass what’s needed. The goal is to avoid hard-coding dependencies inside modules or classes.

How to apply:
	•	Function parameters: If a function needs to use, say, a database or an API client, make it a parameter. For example, instead of:

# Implicit dependency (bad):
import db
def get_user(name):
    return db.connection.query("SELECT ...")

Do:

# Explicit dependency (good):
def get_user(name, db_conn):
    return db_conn.query("SELECT ...")

Now get_user doesn’t magically reach into a module; it uses what it’s given. The calling code (perhaps the web handler) is responsible for passing db_conn, likely obtained from an initialization routine.

	•	Constructor injection (classes): Provide needed components via the __init__. For example:

class UserService:
    def __init__(self, user_repository):
        self.repository = user_repository  # injected dependency
    def get_all_users(self):
        return self.repository.fetch_all()

The UserService is not deciding which UserRepository to use; it’s given one. The wiring happens outside, perhaps in an application factory:

repo = UserRepository(db_connection)
service = UserService(repo)

This pattern clearly separates creation from use, enabling you to swap out UserRepository with a fake in tests, or change its implementation without touching UserService ￼ ￼.

	•	Factories and provider functions: Sometimes manual wiring can be tedious if there are many dependencies. You can use factory functions to bundle creation. For instance, a function create_user_service(config) that inside creates the DB connection, repository, and then the service, returning a fully wired object. This is still explicit – you call create_user_service at the top level of your app (with a config), rather than having hidden module-level assembly.
	•	Framework DI features: Modern frameworks like FastAPI have DI systems that use type hints and decorators to provide dependencies. For example, FastAPI can call functions with parameters that are annotated as dependencies (using Depends(...)), injecting things like a database session automatically per request. Under the hood, this is still explicit in configuration: you define a dependency provider (like a function that yields a DB session from a global engine or sessionmaker) and FastAPI ensures each path operation receives it. This approach avoids needing to import global objects in your endpoint code – you declare needs and FastAPI supplies them. It’s a good example of an ergonomic DI in Python that doesn’t require a large container library.

Benefits: Code becomes more modular and testable. A class or function no longer initializes its own dependencies (which might be complex or slow), so in tests you can pass a lightweight stub or mock. The example in the BetterStack guide showed how injecting a DatabaseConnection into a repository allowed tests to substitute a fake database easily, whereas a hard-coded global connection made that very difficult ￼. Additionally, the system is open to extension – to support a new type of database or multiple databases, you can instantiate different repositories or connections and pass them appropriately, rather than all code being tied to one global connection. This also naturally limits the scope of state: if a function only gets the objects it needs, it can’t inadvertently modify some other part of global state.

Performance impact: Some worry that passing objects around is slower than using globals. In practice, the difference is negligible. Accessing a local variable (or attribute) versus a global variable is actually faster in Python’s execution model (locals are optimized on the stack). The only potential overhead is creating objects to pass in, but if those objects (like a DB connection pool or config object) are created once at startup, then usage is efficient. The clarity and testability gains vastly outweigh micro-performance concerns. As one source notes, Python can implement DI “easily” without significant runtime cost ￼ ￼.

Real-world example: Requests library – Python’s HTTP library – gives you a choice: you can use requests.get(url) which under the hood uses a module-level session, or you can explicitly create a Session object and call session.get(url). The latter is dependency injection in spirit: you manage the session (with custom config, cookies, etc.) and pass it where needed. It’s considered best practice for performance and clarity to use your own Session in applications ￼ ￼. Indeed, the Requests documentation and community advise using explicit Session objects in long-lived programs rather than the convenience global functions ￼. Similarly, boto3 (AWS SDK) defaults to a global session when you call boto3.client('s3'), but the official docs “recommended that in some scenarios you maintain your own session” ￼. In other words, create a Session() and then clients from it, so you can manage credentials and regions explicitly. Experts have written that for any non-trivial program, you “should always use a session directly, rather than the module level functions” ￼ ￼, to avoid implicit global state in your AWS interactions.

2. Configuration as Data, Flowing from the Top

What & Why: Configuration (settings) should be treated as data that is injected into the application at startup, not accessed ad-hoc at runtime from global places. This means reading environment variables, config files, or command-line args in a controlled way (typically in one module or at the entry point), loading them into a configuration object or simple variables, and then passing those into the parts of the application that need them. The aim is to avoid the situation where deep inside module X you call os.getenv("FOO"). Instead, module X should receive foo_value via parameters or via an initialized config object.

How to apply:
	•	Centralize config loading: Have one module (often named config.py or located at the program entry) that knows how to load configuration from external sources (env vars, .ini/.yaml files, etc.). For instance, use Python’s os.environ or libraries like python-dotenv or Pydantic BaseSettings to gather all needed configuration. Do this once during program startup. If using Pydantic (as FastAPI does), you might define:

from pydantic import BaseSettings

class Settings(BaseSettings):
    db_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()  # reads from environment or .env file

This settings object can then be passed to whoever needs config. The key is that after this point, no code should call os.getenv(); they should ask for settings.api_key etc., which is a normal attribute (and can be overridden for tests by instantiating Settings with different values).

	•	Pass config to components: If you have an application factory (as in Flask’s create_app pattern), you often do app.config.from_mapping(config_dict) or similar inside it ￼ ￼. That loads config into the app, and then other parts of the framework (like current_app.config in Flask) can use it. In a more general architecture, you might pass the config object to constructors: e.g., db = Database(settings.db_url), payment_client = PaymentClient(settings.api_key), etc. Higher-level services might not need the whole config, just the pieces relevant to them.
	•	Immutability and constants: Treat configuration as essentially read-only data. Once loaded, it’s not meant to change at runtime (except in special cases like reloading config). This means you can safely share a config object without fear it will be arbitrarily mutated deep in the program. If using plain dictionaries for config, use them in a read-only fashion. This avoids the “who last changed this global setting?” problem.
	•	Multiple environments: Use environment variables or separate config files for different environments (dev, testing, production), but the code path to load them should funnel into the same config object. For example, if an env var ENV is set to “production”, your config loader might decide to read prod.settings.yaml instead of dev.settings.yaml. Either way, the app code just sees a settings object and is unaware of where it came from. This abstracts away environment differences cleanly. Django’s approach traditionally uses separate settings modules (and the DJANGO_SETTINGS_MODULE env var to select one), which works for apps but is less flexible for libraries. Many Django developers now use packages like django-environ or django-configurations to better manage multiple environments without abusing globals ￼ ￼. The key takeaway: don’t scatter environment-specific conditionals throughout your code; handle them at config load time.

Benefits: By flowing config from the top, you ensure every component is explicitly aware of its configuration. This makes it easier to reason about and to test. For instance, in tests you can create a test_settings object (or just override certain values on the config) and initialize your component with it. There’s no spooky action from the environment or missing env vars causing tests to fail – if something is required, it’s likely a field in the config object, and constructing that object will fail loudly if not provided. It also means you can run multiple instances of your application logic in the same process, each with its own config, simply by creating multiple config objects. This is useful for things like parameterized testing or batch processing different inputs.

A concrete benefit was seen in Flask’s design: by switching to an application factory, Flask allows passing in a test configuration when creating the app (the create_app(test_config=...) parameter) ￼ ￼. This allows tests to use a fast in-memory database or special settings easily, without having to monkeypatch environment variables or global objects after the fact. The config is clearly part of app creation, not hidden.

Real-world example: Celery’s configuration – Celery historically allowed configuration via a global celery.conf (the default app’s config). In modern Celery, you instantiate a Celery app with its own config (as shown: app = Celery(); app.config_from_object('celeryconfig') for example) ￼. This means you could have two Celery app instances with different configs if needed. Under the hood Celery still has a default app for backwards compatibility, but they explicitly warn that relying on it can lead to “app instance leaks” that are hard to debug, and even provide a CELERY_TRACE_APP environment variable to catch when code falls back to the default app ￼. This underscores the value of explicit config: Celery encourages you to always pass the app (which carries config) around, rather than using the implicit default. Their move to multiple apps was motivated by the need for clearer state management in larger systems.

Another example: Django vs. FastAPI settings. Django’s settings is a module that is essentially a singleton (you access settings via import). FastAPI, on the other hand, often uses a Settings object (via Pydantic) as shown above. In a FastAPI app, you might declare a dependency on Settings to inject config into path functions. This means pieces of the app can be tested by instantiating a Settings with test values. In Django, to change a setting for a test, you typically use override_settings context manager, which is more global and affects any code running in that context – it works, but is less modular. Thus, even though Django is successful, many projects adopt patterns (like not accessing settings at import, only in functions) to mitigate the global nature ￼. Libraries intended to be used with Django are advised to not cache global settings on import for this reason.

3. Encapsulation of State (Context Objects and Scoped Caches)

What & Why: Not all state can be easily passed through parameters, especially if it’s used widely. For cases where some state truly needs to be shared (e.g., a cache or a connection pool), the recommendation is to encapsulate it in a dedicated object and control its lifecycle explicitly. This could be an application context, a state holder class, or using context managers for temporary state. The idea is to avoid naked module-level globals; instead, wrap state in a class or well-defined singleton with clear usage protocols.

How to apply:
	•	Application context / container: Create a class that holds various resources and pass that around. For example:

class AppContext:
    def __init__(self, config: Settings):
        self.config = config
        self.db_engine = create_engine(config.db_url)
        self.cache = {}
        # etc.

Now, instead of global variables ENGINE or CACHE, you have app_context.db_engine. This app_context can be passed into functions or stored in frameworks that allow contextual globals (Flask actually uses current_app in this way under the hood). The difference from using module globals is that you could have more than one AppContext if needed (for tests or sub-applications), and you can swap out pieces of it (e.g., use an in-memory DB engine in tests by initializing the context differently).

	•	Singletons (the right way): If you truly need a singleton (e.g., a single instance of a configuration or a single thread pool), you can implement it in a controlled manner. For instance, using the Borg pattern (shared state) or simply a module global that is only initialized in a controlled function. The key is to hide the fact it’s global from the rest of the code by not exposing it as a bare global. Instead, provide access functions. Example:

# config_manager.py
_config = None

def get_config():
    return _config

def load_config(path):
    global _config
    _config = parse_config_file(path)

Here _config is module-private. Other code calls config_manager.get_config(). This at least funnels access through one place, where you could add logging or ensure it’s loaded. It’s still effectively global, but you’ve made the dependency obvious (any code using config must import config_manager and call get_config). This is a minor improvement and still not ideal, but it’s better than lots of modules reading environment or having their own global configs. Many libraries accept a singleton config in their API; for instance, some ORMs have a global default connection but allow overriding per call.

	•	Context managers for temporary state: When state is needed only within a certain scope (say, enabling a feature flag or setting a global value for the duration of a task), use a context manager or fixture to encapsulate that change. For example, instead of setting a global variable and manually un-setting it later (risking leakage if an error occurs), do:

from contextlib import contextmanager

@contextmanager
def use_cache(cache_obj):
    global cache
    old_cache = cache
    cache = cache_obj
    try:
        yield
    finally:
        cache = old_cache

Then:

with use_cache(my_test_cache):
    # code that uses the global cache variable
    ...

This ensures the state is reset, and it’s clear in code that within that with block, a different cache is in use. Pytest uses a similar idea with fixtures – you can have a fixture that temporarily sets an environment variable or swaps an object, and Pytest will restore it afterward. This pattern acknowledges global state but contains its impact to a known scope.

Benefits: Encapsulation clarifies ownership of state. Instead of “free-floating” global variables that any code can change, you have objects or contexts that can be passed, replaced, or carefully managed. It also helps with discoverability – if I see a function signature func(ctx: AppContext), I immediately know that it likely needs database or config from that context, versus func() that secretly grabs global stuff. Encapsulation also paves the way for multi-instance support. For example, if one day you want to run multiple “apps” in the same process (like multiple Flask apps or multiple pipelines in parallel), having the state in an object allows that. If everything were module-level, you’d have to re-architect from scratch.

Real-world example: SQLAlchemy – The SQLAlchemy library encourages creating an Engine (database connection pool) and Session objects, rather than hiding database access in globals. In documentation, they often show the engine being created at module import in the user’s application code (and indeed refer to it as typically a module-level singleton in an app) ￼. But the crucial detail is that the library itself does not impose a single global engine; it’s up to the application. Applications that outgrow a single engine can manage multiple by creating multiple engine objects. This is a controlled use of a “singleton” – the app may treat an engine as a globally used object, but it’s still an object that can be passed around, not an implicit part of every query function. Compare that to an alternative design where SQLAlchemy.query("...") implicitly used a global engine; that would be less flexible. In fact, some ORMs (like Django’s ORM) do have an implicit global connection state, which is why using the Django ORM outside of a Django project requires extra setup. SQLAlchemy’s approach is more explicit.

Another example: Pytest fixtures serve as context providers. Instead of writing tests that rely on global state, you write fixtures that supply the state to the test or the system under test. For instance, a fixture might create a temporary file and set an env var pointing to it, then yield. The test using it doesn’t call os.getenv directly; it receives the relevant path via fixture injection. This is effectively dependency injection for tests, using contexts to manage global-like state. If our application follows suit by avoiding direct global usage, it aligns naturally with such testing patterns.

4. Import Discipline and Module Design

What & Why: To avoid the “import-time pitfalls,” adopt import discipline: modules should primarily contain definitions (classes, functions, constants) and minimal side effects. Heavy operations should be moved to runtime, under explicit control. Also, manage imports to reduce unnecessary coupling and performance costs: import only what you need, when you need it (but don’t abuse dynamic imports to hide design issues).

How to apply:
	•	No import-time I/O: Do not open files, connect to databases, or perform network calls at import. If you need to load a small default dataset, consider lazy-loading it on first use or provide a helper function to load it. For example, if a module provides a lookup table loaded from a file, don’t load it at import. Instead, load it in a function the first time it’s requested, and possibly cache it. This way, if a user never calls that function, the file is never read. This follows the guideline given by experts: “global objects should wait until they’re first called before opening files or creating sockets” ￼.
	•	Guarded initialization: If some setup must happen at import (perhaps registering a plugin or initializing a small cache), document it clearly and keep it quick. Often a better approach is to expose an initialize() function and have the application call it. For instance, many libraries that require heavy setup (like scheduling jobs or setting up thread pools) ask the user to call init() at program start. This makes the dependency explicit in the startup sequence.
	•	Selective imports for performance: If your module has optional functionality that brings in heavy dependencies, consider lazy importing those inside the relevant function. This is acceptable when done deliberately for performance or optional-dependency handling. For example, say your library can use either Pillow or OpenCV to process images, but not all users need image processing. You might delay import cv2 until someone calls the function that needs it. This avoids penalizing users who never use that part. The key is to balance this with clarity – document that your function may raise ImportError if the optional dependency isn’t installed, and handle that gracefully. This technique was even suggested in the PyDev “import the world” discussion: to reduce startup costs, avoid top-level imports of everything, and import within functions for optional features ￼. But note, this should not be misused to hide core dependencies.
	•	Avoid circular imports via design: Sometimes dynamic imports are used to break circular references. A better fix is often to refactor code structure – e.g., move common functionality to a third module that both import, or redesign class responsibilities to not be cyclic. If you must use a local import to solve a circular dependency, limit it to that case and add a comment explaining it. This makes it clear it’s a conscious choice, not an accidental pattern to be copied.

Benefits: Good import discipline ensures faster startup, fewer surprising failures, and easier understanding of code. When a module loads quickly and quietly, you can import it in a REPL or tooling without side effects. For example, tools that auto-import modules (like test runners, or IDE indexers) won’t accidentally trigger some heavy operation. Additionally, by not pulling in everything at once, you reduce memory overhead and possibly avoid import-related deadlocks or race conditions in multi-threaded startup (a rare issue, but real in some scenarios when imports happen in parallel threads).

From a maintainability standpoint, keeping imports at top-level except for rare cases makes dependencies visible. It answers “what does this module use?” by just reading the top. This aligns with Python’s design where import is explicit.

Real-world example: CLI tools like Mercurial or even Python’s own pip have historically struggled with import cost, because a CLI command often has to import a lot of modules. Developers of these tools sometimes employ lazy loading of subcommands – essentially not importing all submodules until needed, to improve responsiveness ￼ ￼. The Mercurial example (mentioned in the PyDev blog) had to “hack around” import times for a better user experience ￼. By structuring the application as “small core + plugins loaded on demand,” they achieved better performance. This is an advanced use of import control that might not apply to every project, but it’s good to be aware of.

Another example is the standard library’s logging module: it defines logger classes and basicConfig, but it doesn’t, for instance, start writing logs to a file upon import. The user has to configure it. This is by design – imagine if import logging created a file app.log in the working directory! That would be unexpected. Instead, you call logging.basicConfig in your main if you want that. Libraries should emulate this principle: import should set up definitions, and any action should be invoked by the user.

⸻

Combining these recommended patterns yields an architecture where:
	•	The application entry point loads configuration and constructs necessary objects (database connections, clients, etc.).
	•	It then injects these into the rest of the application, either by passing them as parameters or storing them in a context that is passed around.
	•	Each module or component clearly states what it needs through its interface, rather than reaching out to grab things.
	•	Global state is minimized to constants or truly application-wide singletons which are managed in one place.
	•	Imports are clean, and initializing the program is a deliberate act (running a function, creating an object) rather than incidental on first import.

With these patterns established, let’s examine some brief case studies of existing projects or scenarios, to see how they navigate these issues and validate the recommendations.

Case Studies

Case Study 1: Flask vs. Django Configuration

Django: Django uses a global settings object approach. You set an environment variable DJANGO_SETTINGS_MODULE and Django loads that Python module as settings. Any Django code or plugin can import django.conf.settings to get config. This is convenient in a single Django app, but as noted, it effectively means configuration is a module-level singleton. Third-party Django apps often followed suit, reading from settings at import to set defaults ￼. This caused issues for testability (see the earlier example where overrides didn’t work because of import timing). Django’s pattern works for full applications – you typically run one Django app per process – but it’s problematic for libraries, which should ideally be usable outside the Django context or at least not break Django’s own testing mechanisms. As a result, well-behaved Django apps do minimal work at import (maybe define default values as module constants) and fetch from settings in functions or on-demand. Django itself provides utilities like django.test.override_settings to temporarily change the global settings for tests, indicating the need to work around the rigidity of a global config.

Flask: Flask’s design moved away from a process-wide singleton app to an application factory pattern. In early Flask examples, you’d often see app = Flask(__name__) at the module top, which is fine for simple cases but can become limiting. The official docs now promote creating the Flask app in a function and configuring it there ￼. Extensions in Flask (like Flask-Mail, Flask-Login) are often designed to be initialized with the app (e.g., mail = Mail(app) or Mail().init_app(app)) rather than grabbing global state. This means they support multiple apps or factory use. Flask does have the current_app global proxy, but that is only active within an active request or application context – using it in library code outside a request is an error. This forces a bit of discipline: you can’t just call current_app anywhere unless you’re sure you’re in a request. So while Flask provides a global-ish mechanism for convenience, it’s bounded by context and usually only in the web handling layer. Deeper layers of a Flask app (service modules, database code) typically receive what they need via the app or config object passed in at init. The Flask approach is generally considered more test-friendly than Django’s, at the cost of a bit more boilerplate in setting up an application.

Takeaway: Django’s global settings pattern demonstrates how global config can simplify usage at first but complicate certain scenarios (testing, reusability). Flask’s explicit app instance pattern shows that even in a framework known for simplicity, the benefits of explicitness were compelling enough to influence its recommended practices. Our project, being more library-like in parts, should emulate Flask’s and FastAPI’s explicit config passing rather than Django’s implicit global settings (except perhaps at the very highest application level).

Case Study 2: Celery’s Refactor from Global to Instance

Celery is a distributed task queue. In Celery 4.x and earlier, one could simply do from celery import Celery; celery.send_task(...) without ever explicitly creating an app – Celery had a default app instance. While convenient, this led to a situation where any library that imported Celery could inadvertently use or configure the default app, interfering with the real app configuration. It also made multiple apps impossible in one process (all tasks would attach to the default singleton).

In the “Big Instance” refactor, Celery introduced a requirement (and encouragement) to always create your own Celery() app instance ￼. Now you do:

app = Celery('myapp')
app.config_from_object('celeryconfig')
app.autodiscover_tasks()

and you use that app to send tasks or start workers. Under the hood, Celery still maintains a celery._default_app for legacy use, but they clearly warn that relying on it is error-prone ￼. They even provide a debug flag CELERY_TRACE_APP which will throw an error whenever code falls back to the default app, helping developers locate places in their code that weren’t given an app and implicitly grabbed the global ￼. This is essentially a tool to enforce explicit DI of the app instance.

This case study validates a few points:
	•	A project can start with a global state design (for ease of use) but later realize the need for explicit instances as it scales.
	•	Backwards compatibility concerns may force keeping some global around, but the long-term strategy is to deprecate and remove it (Celery’s docs indicate many old aliases to global things are pending deprecation ￼ ￼).
	•	The effort required to do this (a major refactor across the library and user code) is substantial – hence the motivation to avoid introducing such globals to begin with in new projects.

For our contributors, Celery’s story is a cautionary tale: it’s better to require an extra step of creating/passing an object now than to fix a global-state design later when it’s deeply ingrained.

Case Study 3: boto3 and Requests – Convenience vs. Best Practice

We touched on these briefly, but let’s explicitly compare:
	•	boto3 (AWS SDK): Out of the box, developers can import boto3; boto3.client('s3') and it magically works by reading config from environment or AWS config files. Internally, this calls _get_default_session() to either retrieve or create a global session ￼ ￼. For quick scripts, this is fine. However, for robust applications (especially ones that might use multiple AWS accounts or run in multi-threaded environments), the boto3 docs and experts recommend creating your own Session object ￼. This allows explicit control of credentials (you might load them yourself, or use different profiles) and avoids thread-safety issues with the default session. The design here acknowledges both ease-of-use and the need for explicit state: they provide the foot-gun (global session) but clearly signpost that advanced usage should manage state explicitly ￼ ￼. Our project should lean toward the explicit side from the start, given we target maintainability.
	•	Requests: Similar pattern – convenience vs control. If you call requests.get(), under the hood it creates a new Session or uses a module-level one for you. But advanced usage is to make a Session, perhaps attach an adapter or set timeouts, and pass it around. One downside of the convenience in requests is that many beginners overuse requests.get in a loop and unknowingly lose out on performance (since a new connection is made each time, instead of reusing one). The library docs encourage session reuse to leverage connection pooling ￼ ￼. The principle: an explicit object (Session) carries state (cookies, connections) that is better than a hidden global pool.

Takeaway: Providing quick shortcuts can be okay, but they often become the path of least resistance that people stick to, sometimes to their detriment. In our contributor guide, we likely don’t need to provide such shortcuts; we prefer patterns that scale. If we do have any globally convenient APIs, we should document their limitations and encourage the explicit approach for anything non-trivial.

Case Study 4: Pytest’s Fixture Injection

Pytest isn’t an application, but its design showcases the power of injection. Tests often need to set up state. Rather than relying on global state or explicitly calling setup functions in each test, pytest uses fixtures which are basically functions that return a resource and can be requested by test functions. For example, a test can declare def test_api(client): ... if there’s a client fixture that provides a test HTTP client. Pytest will inject it. Under the hood, fixtures can depend on other fixtures, creating a dependency graph that pytest resolves.

The key point: pytest discourages global state by providing a structured injection system. If you find yourself using a global in tests (like a module variable modified by tests), it’s usually better to make it a fixture so pytest can manage its life cycle (setting it up, tearing it down). This aligns with our guidance for application code: pass things in, don’t rely on global variables that might persist between test runs.

One direct lesson from pytest: it’s trivial to spin up multiple instances of something if you avoid global reliance. For example, you can parametrize a fixture to create different configs and run the same test function with each config. If the code under test reads a global config, that’s much harder – you’d have to swap globals and ensure no bleed-over. With injection, each test case is isolated by getting its own fresh inputs.

In summary, these case studies reinforce: projects that embraced explicit state and config (FastAPI, modern Flask, Celery 5, etc.) have reaped benefits in flexibility and testability. Projects that started with implicit state (Celery older versions, some Django patterns) eventually felt pain and moved towards more explicit patterns. Following the recommended patterns from the start positions our project to avoid those growing pains.

Implementation Guidelines

This section translates the above principles into concrete guidelines and examples for our contributors. It serves as a “how-to” for implementing the recommended patterns and avoiding the anti-patterns. We include code snippets illustrating the DOs and DON’Ts.

1. Provide Config at Application Boundaries
	•	DO load configuration in a controlled way at the program’s entry point (for example, in the if __name__ == "__main__": block of a CLI script, or in the startup script of a web service) and pass it to your components. Use a structured object or dictionary for clarity.
	•	DON’T call os.environ or os.getenv throughout your code. Also, don’t read files or databases in module scope for configuration.

Example – Configuration:

# config.py -- recommended approach
import os
class Config:
    def __init__(self):
        self.api_url = os.getenv("API_URL", "https://api.dev.local")
        self.db_url = os.getenv("DB_URL", "sqlite:///dev.db")
        self.debug = bool(os.getenv("DEBUG", False))

# main.py
from myapp import app, Config
config = Config()                # Load once
application = app.create_app(config)  # Inject into app creation
application.run()

In this example, create_app will use config to configure the app (set up database connections, etc.), and then throughout the app, components can either access needed values from a passed reference or be closed over them.

Contrast with a DON’T scenario:

# Bad practice: deep inside some module
import os
API_URL = os.getenv("API_URL", "https://api.dev.local")  # at import time

def fetch_data(id):
    response = requests.get(f"{API_URL}/data/{id}")
    ...

Here API_URL is evaluated when the module is imported. If in a test you want to use a different URL, setting an env var after import does nothing. The function fetch_data implicitly uses global state. Instead, it should accept the URL or a session as an argument.

2. Explicit Resource Management
	•	DO pass shared resources (database connections, clients, etc.) to the code that uses them. Ideally manage their lifecycle (open/close) in one place.
	•	DON’T open connections or create heavy objects at import, nor scatter their initialization across the codebase.

Example – Database Session (SQLAlchemy):

# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def init_db(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return engine, Session

# repository.py
class UserRepository:
    def __init__(self, session_factory):
        self.Session = session_factory

    def get_user(self, user_id):
        with self.Session() as session:
            return session.get(User, user_id)

Usage:

engine, Session = init_db(config.db_url)
user_repo = UserRepository(Session)
service = UserService(user_repo)

In tests, you could call init_db("sqlite:///:memory:") to get a lightweight in-memory DB and pass that Session factory to your repository. The repository does not itself decide how to get a session; it’s provided, making it easy to sub in a different one (or even a fake session object) for testing.

By contrast, a DON’T example:

# Bad: global engine and session creation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.getenv("DB_URL"))        # at import
Session = sessionmaker(bind=engine)

def get_user(user_id):
    session = Session()      # uses global engine implicitly
    return session.get(User, user_id)

This code will execute the database connection setup as soon as the module is imported, possibly throwing an error if DB is unreachable and making any import of this module potentially crash the program. Testing this function would either hit a real database or require patching the global Session – neither is ideal.

3. Use Context and Dependency Injection for Testing
	•	DO design your functions and classes so that in tests you can easily substitute real components with fakes or mocks. If a function calls an external API via a client object, ensure that client is passed in or accessible via an instance attribute that tests can monkeypatch or replace.
	•	DON’T hard-code calls to external services or global singletons in your logic without a way to override them.

Example – HTTP Client Injection:

# service.py
class PaymentService:
    def __init__(self, http_client):
        self.http = http_client

    def charge(self, user, amount):
        resp = self.http.post(self._url("/charge"), json={"user": user, "amount": amount})
        return resp.status_code == 200

    def _url(self, path):
        return self.http.base_url + path

# main.py
import requests
payment_service = PaymentService(http_client=requests)  # using requests as the client

Here, PaymentService uses whatever is passed as http_client. We could pass the requests module itself since it has a .post function and a base_url attribute could be configured, or better a requests.Session instance with a preset base URL. In tests, we can create a dummy client:

class DummyClient:
    def __init__(self):
        self.base_url = "http://testserver/api"
        self.called = False
    def post(self, url, json):
        self.called = True
        return type("Resp", (), {"status_code": 200})()  # dummy response object

dummy = DummyClient()
service = PaymentService(dummy)
assert service.charge("user1", 100) is True
assert dummy.called  # verify that the dummy client's post was used

No actual HTTP call occurred. If the code had instead done requests.post(...) inside charge(), we’d have to monkeypatch requests.post globally to test it, which could affect other tests. By injecting, we contain the change.

Another scenario: Pytest fixtures can help manage global state. Instead of a function relying on a global cache, design it to accept a cache or have a way to set it. For instance, a search function might accept a cache dict to store results. In production you pass a module-level cache, in tests you pass an empty dict and inspect it. Designing with injection at small scales like this accumulates to a testable architecture at large.

4. Linting and Automated Checks

To ensure these practices, we can employ linting rules:
	•	Mypy/Type hints: By using type hints for dependencies, mypy can catch if you forgot to pass a required argument (for example, if a function signature changes to require a config and you don’t update a call, mypy flags it). While mypy doesn’t directly forbid globals, writing code with explicit parameters naturally leads to better-typed function signatures.
	•	Flake8/Ruff rules: We can enable or create lint rules to detect some anti-patterns:
	•	Flag use of the global statement within functions (pylint rule W0603) – in our project, there should be little need for that except perhaps in rare singleton modules ￼ ￼.
	•	Flag modules that perform certain side effects at import (this is harder to detect statically, but even a simple check for os.getenv calls at module level could be a heuristic).
	•	The flake8-global-variables plugin can warn when a global variable is defined (especially if mutable) ￼. We might integrate that to catch unintended global state.
	•	Encouraging small pure functions and using tools like ruff to catch unused imports or variables can indirectly push developers to not rely on external state.

By integrating these tools in CI, we automatically discourage slipping back into bad habits.

5. Documenting Patterns in the Guide

We will update our Contributor Guide with a section on State and Configuration Management that includes:
	•	A summary of why global state is dangerous (with a brief example as given in this report).
	•	Rules such as:
	•	“No import-time side effects: Imports should not perform I/O or alter global program state.”
	•	“No hidden dependencies: A module or function that needs something should accept it or clearly document that it uses an external resource.”
	•	“Singletons only by necessity: If you must use a singleton (e.g., a cache or thread pool), wrap it in an interface that can be overridden for tests, and do not directly import the singleton in every module.”
	•	“Pass config explicitly: Functions and classes that need config values must get them via parameters or via an injected context. Do not directly read environment variables except in the dedicated config module.”

Each rule will have a “why” explanation, often referencing testability. For instance, “We require explicit config passing because it allows test code to run components under different settings without unwanted interaction between tests ￼ ￼.”

We’ll also add example snippets in the guide showing correct vs incorrect usage, similar to those above. Real examples from our codebase (anonymized if needed) can illustrate, e.g., how a global cache caused a bug and how we refactored it to a context.

6. Migration Strategies

For existing code that violates these rules, we’ll outline how to migrate incrementally:
	•	Identify modules with module-level state or heavy import behavior.
	•	Refactor in stages: first, encapsulate the global in a function or class (even if internally it’s still global, reduce direct access). Then, change call sites to pass things in.
	•	Use deprecation warnings if removing a global API that external code might use.
	•	Write tests around old behavior if not already, to ensure the refactor doesn’t change outcomes.

We can include a concrete plan: for example, “Phase 1: Wrap settings usage – introduce a get_setting(key) function and replace direct settings.X with it, so we have a single choke point. Phase 2: Change get_setting to use an injected config rather than global.”

The Contributor Guide should reassure that these changes are for long-term stability, and while they might introduce a bit more verbosity, they prevent much worse problems down the line.

Contributor’s Guide Updates

To incorporate these findings into our Contributor’s Guide, we will add or update sections with the following content:

Section: Application State and Configuration

Guideline 1: No Hidden State via Module Globals
Do: Keep state within object instances or passed as function arguments. For shared state (caches, singletons), define them in one module and provide access functions or context managers.
Don’t: Define mutable global variables at module import for use in other modules. For example, do not have mycache = {} at the top of a module that other code imports and modifies. Instead, if a cache is needed, encapsulate it in a class or have a controlled getter/setter.

Rationale: Module globals create implicit couplings that make the code hard to understand and tests prone to interference ￼ ￼. By accessing state through functions or objects, you localize the impact and can later replace the implementation (e.g., swap a dict for a LRU cache object) without changing every usage.

Guideline 2: Explicit Configuration Passing
All functions or classes that need configuration should get it from parameters or a passed-in config object. Our project has a Config class (or similar) – use it. If a new config value is needed deep in the code, thread it through from the top rather than calling os.environ at that point.

Rationale: This ensures that running two instances with different configs is possible (for testing or future requirements) and that the source of truth for config is centralized ￼ ￼. It also aligns with the “explicit over implicit” philosophy ￼.

Guideline 3: Import Hygiene
Modules should not execute significant logic on import. Do not start threads, open network connections, read large files, or modify global settings when a module is imported. If initialization is required, put it in a function (e.g., initialize() or the constructor of a class) and document that the user should call it.

Rationale: Code that runs on import can cause unexpected failures and performance hits ￼ ￼. This rule keeps imports safe and side-effect free, which is critical for both debugging and performance (e.g., faster test suite startup, ability to import modules in any order without side-effects).

Guideline 4: Testing and Singletons
Any singleton or globally-used object must have a way to be overridden or substituted in tests. If you implement a singleton pattern (like a module that manages a single instance of something), also provide a function or context manager to reset or replace it (for example, a set_instance_for_testing(obj) or similar, which tests can use).

Rationale: This prevents scenarios where tests cannot run in parallel or leave residue because a global wasn’t properly isolated ￼ ￼. It enforces thinking about state lifecycle explicitly. Ideally, avoid singletons altogether in favor of dependency injection, but if used, this is a safety valve.

Guideline 5: Use Framework Facilities Appropriately
If using frameworks that offer contexts or dependency injection (Flask, FastAPI, etc.), leverage those instead of inventing new globals. For instance, in a Flask view, get config via current_app.config (which is provided by Flask’s context) rather than a custom global. However, limit such usage to the boundaries (views), and within your core logic, keep using explicit parameters.

Rationale: Frameworks have well-tested ways to manage request or app state; using them avoids reinventing the wheel. But mixing framework globals into core logic makes that logic non-reusable outside the framework. By confining framework-dependent state to the edges, we keep the core clean.

Section: Examples of Forbidden Patterns

We will add a small table or list in the guide contrasting bad vs good patterns, distilled from this report, e.g.:
	•	Global config access in library code: (Bad) value = os.environ["VALUE"] in middle of function. (Good) Function signature becomes def func(value, ...) and caller passes os.environ["VALUE"] or config.value.
	•	Mutable default arguments or singletons: (Bad) Using a mutable default like def func(x, cache={'seen': set()}): ... which persists across calls. (Good) Use None default and inside do cache = cache or {'seen': set()} or better, require the caller to provide the cache if needed.
	•	Dynamic imports to hide dependencies: (Bad) def func(): import heavy_lib; heavy_lib.do_things(). (Good) Import at top, or document clearly if lazy-loading heavy_lib is truly necessary, and ensure it’s only for optional functionality.

Each forbidden example will be accompanied by one or more allowed refactored forms. We’ll draw on some of the code snippets we developed in this report for those examples.

Finally, the Guide will have a brief explanation that following these patterns is mandatory for contributions because it ensures that our codebase remains scalable and robust. We’ll mention that these guidelines come from industry best practices and lessons learned from other frameworks (with maybe a link to this research document or summary of it, so contributors understand the “why” not just the “what”). By enforcing these rules, we ensure new code doesn’t introduce hidden complexity that will bite us later.

⸻

Sources: The above recommendations are grounded in widely accepted Python best practices and are informed by experiences from projects like Django, Flask, FastAPI, Celery, Requests, and boto3. For instance, Python experts note that “every global object courts dangers in return for convenience” ￼ and advise designing functions to accept arguments instead of reaching for globals ￼. Flask’s documentation explicitly favors application factories over global app instances to avoid growth pain ￼. Even AWS’s boto3 docs encourage managing your own session for better control ￼. These principles ensure that our code remains explicit, predictable, and testable, aligning with the core philosophies of Python development.