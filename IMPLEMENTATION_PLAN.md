# Implementační plán pro L.O.N.G.I.N.

Tento dokument popisuje podrobný plán implementace pro aplikaci **L.O.N.G.I.N.** (Logical Orchestrated Networked Generative Intelligent Nexus). Plán je rozdělen do šesti hlavních fází, které na sebe logicky navazují a pokrývají všechny aspekty vývoje od základní infrastruktury až po finální nasazení.

---

## Fáze 1: Základní Infrastruktura a Architektura

**Cíl:** Vytvořit pevné základy aplikace, definovat klíčové datové struktury a připravit prostředí.

1.  **Inicializace Projektu:**
    *   Vytvoření adresářové struktury podle `README.md`.
    *   Nastavení správy verzí (Git) a konvencí pro commity.
    *   Vytvoření základních konfiguračních souborů.

2.  **Definice Základních Abstraktních Tříd:**
    *   Implementace abstraktních tříd `LonginModule`, `LonginConnector` a `LonginAdapter` podle souboru `src/longin_core/base/definitions.py`. Tyto třídy budou sloužit jako kontrakty pro všechny budoucí komponenty.

3.  **Nastavení Databázového a Cache Prostředí:**
    *   Spuštění služeb `postgres` a `redis` pomocí poskytnutého `docker-compose.yml`.
    *   Vytvoření databázového schématu pro PostgreSQL, včetně tabulek pro ukládání dat a rozšíření `pgvector` pro sémantické vyhledávání.

4.  **Implementace Vrstvy pro Úložiště (`StorageManager`):**
    *   Vývoj `StorageManager` (`src/longin_core/storage/manager.py`), který bude dynamicky spravovat různá úložiště.
    *   Implementace konkrétních tříd pro úložiště: `JsonStore`, `RedisStore`, `PostgresStore` a `PostgresVectorStore`.

5.  **Implementace Komunikační Sběrnice (`LONGINEventBus`):**
    *   Vývoj asynchronní event bus (`src/longin_core/event_bus.py`) pro komunikaci mezi moduly na stejné hierarchické úrovni.

---

## Fáze 2: Jádro Systému a Orchestrace

**Cíl:** Zprovoznit centrální řídící komponenty a umožnit komunikaci a provádění úkolů.

1.  **Implementace MCP Serveru (`MCPServer`):**
    *   Vývoj `MCPServer` (`src/longin_core/mcp/server.py`) pro komunikaci mezi agenty a nástroji.
    *   Implementace mechanismu pro dynamické načítání pluginů z adresáře `src/longin_core/mcp/plugins/`.

2.  **Vytvoření Základních MCP Pluginů:**
    *   Implementace prvních pluginů pro základní operace, např. `file.read`, `file.write`, `docker.run`, které budou agenti využívat.

3.  **Implementace Centrálního Orchestrátoru (`CoreOrchestrator`):**
    *   Vývoj `CoreOrchestrator` (`src/longin_core/orchestrator/main.py`), který bude zodpovědný za:
        *   Inicializaci a správu životního cyklu všech modulů a agentů.
        *   Start a stop systémových služeb (`StorageManager`, `LONGINEventBus`, `MCPServer`).
        *   Registraci a načítání modulů a agentů.

4.  **Vstupní Bod Aplikace (`main.py`):**
    *   Dokončení `main.py` pro správnou inicializaci a spuštění `CoreOrchestrator`.

---

## Fáze 3: Implementace Inteligentních Agentů

**Cíl:** Vytvořit specializované agenty, kteří budou tvořit "mozek" aplikace a vykonávat klíčové operace.

1.  **`GarbageCollectorAgent`:**
    *   Implementace agenta pro správu kontextového okna (limit 512 tokenů) podle `src/longin_core/agents/garbage_collector.py`.

2.  **`ContextMasterAgent`:**
    *   Agent pro správu kontextu, RAG a práci s vektorovou databází (`src/longin_core/agents/context_master.py`). Bude využívat `StorageManager` a `PostgresVectorStore`.

3.  **`TestOracleAgent`:**
    *   Agent zodpovědný za generování a správu testů na základě specifikací (`src/longin_core/agents/test_oracle.py`).

4.  **`CodeAlchemistAgent`:**
    *   Agent pro iterativní vývoj a refaktoring kódu, dokud neprojdou všechny testy (`src/longin_core/agents/code_alchemist.py`).

5.  **`VisualValidatorAgent`:**
    *   Agent pro vizuální kontrolu UI. Bude potřebovat MCP plugin pro interakci s prohlížečem (např. přes Playwright/Puppeteer). Viz `src/longin_core/agents/visual_validator.py`.

6.  **`SuccessMonitorRecorderAgent`:**
    *   Agent pro zaznamenávání úspěšných pracovních postupů do znalostní báze (`src/longin_core/agents/success_monitor_recorder.py`).

7.  **`CodingFlowBossAgent`:**
    *   Implementace hlavního orchestračního agenta, který řídí celý FRTDSD cyklus a koordinuje ostatní agenty (`src/longin_core/agents/coding_flow_boss.py`).

---

## Fáze 4: Vývoj Frontendového Rozhraní

**Cíl:** Vytvořit intuitivní uživatelské rozhraní pro interakci se systémem L.O.N.G.I.N.

1.  **Nastavení Frontend Projektu:**
    *   Vytvoření nového projektu pomocí `React` (nebo `Next.js`).

2.  **Základní UI Layout:**
    *   Vytvoření hlavního rozložení aplikace podle přiloženého obrázku (černé pozadí, zelené okraje, hlavička, levý panel, hlavní obsah, vstupní pole).

3.  **Implementace Klíčových Komponent:**
    *   `ThinkingIndicator.tsx`: Komponenta pro zobrazení stavu "přemýšlení" agentů.
    *   `useGIFIndicator.tsx`: React hook pro správu viditelnosti indikátorů.
    *   Chatovací modul pro konverzaci s agenty.
    *   Komponenty pro výběr Providera a Modelu v hlavičce.

4.  **Propojení s Backendem:**
    *   Navázání komunikace (pravděpodobně přes WebSocket nebo gRPC spravované `MCPServer`) pro real-time aktualizace stavu a zobrazování výsledků od agentů.

---

## Fáze 5: Integrace a End-to-End Testování

**Cíl:** Propojit všechny části systému a ověřit jejich správnou funkčnost v reálných scénářích.

1.  **Kompletní Integrace:**
    *   Propojení `CoreOrchestrator` s agenty a následně s frontendem.
    *   Zajištění, že akce uživatele ve UI správně spouští FRTDSD cyklus řízený `CodingFlowBossAgent`.

2.  **End-to-End Testování:**
    *   Provedení prvního kompletního testu: zadání jednoduchého úkolu (např. "Vytvoř v UI tlačítko s textem 'Test'") a sledování celého procesu od generování testů až po vizuální validaci.

3.  **Vývoj Webového Instalátoru:**
    *   Podle `design-documents/` vytvořit samostatnou SPA (Single Page Application) pro instalaci a konfiguraci L.O.N.G.I.N.

4.  **Tvorba Testů:**
    *   Psaní jednotkových (unit) a integračních (integration) testů pro všechny klíčové moduly a agenty.

---

## Fáze 6: Nasazení a Dokumentace

**Cíl:** Připravit aplikaci pro produkční nasazení a finalizovat veškerou dokumentaci.

1.  **Kontejnerizace Aplikace:**
    *   Vytvoření `Dockerfile` pro každý modul a službu.
    *   Rozšíření `docker-compose.yml` o všechny aplikační služby pro snadné lokální spuštění.

2.  **Nastavení CI/CD Pipeline:**
    *   Automatizace procesů sestavení (build), testování a nasazení (deployment).

3.  **Finalizace Dokumentace:**
    *   Doplnění a aktualizace veškeré technické a uživatelské dokumentace v adresářích `docs/` a `design-documents/`.
    *   Vytvoření podrobné API dokumentace pro všechny externí i interní rozhraní.
