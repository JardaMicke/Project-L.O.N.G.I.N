Projekt longine se skládá z jednotlivých malých modulů z nichž Každý má svojí specifickou funkci. Jednotlivé moduly jsou propojeny konektory které fungují na eventBus. Jednotlivé moduly se skládají do větších celků pro spolupráci na fungování jako celek.

Máme několik stupňů modulů. Nejvyšší je augment ten reprezentuje hotový modul funkční pro připojení na core. Skládá se z komponentů.

Component - menší stupeň Skládá se z units.

Unit - menší stupeň  Skládá se z parts.

Part - menší stupeň základní modul ze kterého se pak skládají další a další moduly pomocí napojení přes konektory.

Konektor - jednoduchý mini modul který přijme určitá data zvaliduje je z verifikuje je přetransformuje na typ který potřebuje následující modul Pokud to jde A odešlemu je všechno To bude dynamické a pokud to bude optimální i asynchronní. Každá spojka bude odesílat do logu jméno modulu ze kterého jdou data Jaká jdou data a jméno modul do kterého jdou data A jaká odcházejí data.  Vyšší stupně modulů mezi sebou budou mít i vyšší stupně konektoru pojmenujeme později. Na vyšších stupních konektorů budou moct být napojené diagnostické programy Nebo například výhybky pro připojení více modulů zároveň.. 

 Hlavní složka projektu se jmenuje "L.O.N.G.I.N.".

Základní funkcionality Core. Základní modul longina neboli core se skládá ze skeneru http elementů, pole na zobrazení načtených elementů, funkce vybrání cesty k uložení souborů na harddisk, funkce ukládání jednotlivých načtených elementů do předem určených skupin, funkce identifikace jednotlivých dat příchozích a jejich třídění do jednotlivých souborů. Funkcionalita ukládání souborů a vytváření složek. Funkce vybrání jednoho nebo několika souborů a jejich odeslání společně s otázkou zpět do Ai, funkce možnost odeslat otázku, funkcionalita diktovat a přepisovat na text do kteréhokoliv textového pole v prohlížeči i ve Windows, detailně nastavitelná funkcionalita text to speech ve stylu co pouze se má převádět na řeč. 


UI a jeho plná funkcionalita pro všechny funkce, černé pozadí, tlusté zelené okraje, funkce UI umožňující připíchnout si taby do velikosti 2x2 čtverce UI V případě spojení bude Hlavní okno vlevo nahoře a taby záložek pouze u pravého horního čtverce. Kore okno je vždy připíchnuté a vždy nahoře, Můžou se na něm přepínat jednotlivé záložky ale v okamžiku připíchnutí jedné ze záložek se připíchne napravo od Kore okna druhé připíchnuté podkore okno a třetí připíchnuté doprava dolů. Pro připichování oken bude v pravém horním rohu každé záložky Kromě core záložky checkbox po jehož zaškrtnutí se aktuální Tab připíchne. Jakmile budou tři taby připíchnuté checkbox zmizí na všech kromě připíchnutých. Pokud nebude okno připíchnuté bude možnost z pravé spodní roh okno zvětšovat a zmenšovat až do této minimální velikosti 1200*800. Tlačítko aktivního tabu bude mít uprostřed zelený čtvereček.

Jako basic Button bude vypadat každé tlačítko vždy bude mít vedle sebe na levé straně status světýlko které bude při neaktivitě šedé při aktivitě zelené a při chybě červené. V pravé části bude vždy Label tlačítka. Při stavu kdy je tlačítko stisknuto se prohodí barvy textu a pozadí při puštění tlačítka se barvy otočí zpět.

Všechna textová Pole se vždy budou zobrazovat jako zelený text na černém poli.

Základní teoretický koncept.
Takový má tenhle projekt prostě vytvořit základní jádro který bude schopný se připojit na různé internetové stránky a načítat z nich různé informace konkrétně to bude připraveno pro i asistenta textového a bude to mít kolem sebe různé nastavovací moduly který budou schopný vytvářet lepší instrukce lepší personalizaci A rozhodně lepší Performance a více způsobů využití AI asistenta orchestrace jednotlivých i asistentů podle jejich předností, limitů a limitů volání API. Sdružování velkého množství AI zdarma a hlídání limitů a jejich maximálního využití při jakékoliv práci umožní to obyčejnému uživateli využívat spoustu zdarma AI při stabilní nastavení a personalizaci přes tento adaptér. Sdružení několika adaptérů bude možné vytvořit velmi výkonné výpočetní sítě na vyhledávání či diagnostiku nebo analýzu. kooperace více AI asistentů při plnění jakéhokoli ukolu. 

Vybraný způsob implementace:
Hybridní komunikační systém
Nižší úrovně (Part a Unit)
Pro nižší úrovně (Part a Unit) doporučuji použít kombinaci:
Rozšířený EventBus
Implementace hierarchického EventBus systému pro rychlou a efektivní komunikaci mezi blízce souvisejícími moduly1.
Každý Part a Unit bude mít vlastní instanci EventBus, která je propojena s nadřazenou úrovní.
Sdílený stav
Využití sdíleného stavu pro rychlý přístup k často používaným datům mezi Parts a Units1.
Implementace pomocí thread-safe datových struktur pro zajištění bezpečnosti při souběžném přístupu.
Vyšší úrovně (Component a Augment)
Pro vyšší úrovně (Component a Augment) navrhuji komplexnější řešení:
Message Queue
Implementace systému front zpráv pro asynchronní komunikaci mezi Components a Augments1.
Zajistí škálovatelnost a odolnost při vysokém zatížení.
Middleware
Vytvoření middleware vrstvy pro zpracování a transformaci dat mezi Components a Augments1.
Umožní centralizované zpracování, validaci a směrování dat.
RESTful API
Interní RESTful API pro komunikaci mezi Augments a Core1.
Poskytne flexibilitu pro budoucí rozšíření a možnost nezávislého škálování jednotlivých Augments.
Implementace
Konektory
Využití stávajících konektorů jako adaptérů mezi různými komunikačními mechanismy1.
Konektory budou zodpovědné za validaci, verifikaci a transformaci dat mezi různými úrovněmi komunikace.
Logování
Zachování stávající funkcionality logování v konektorech pro diagnostické účely1.
Asynchronní zpracování
Implementace asynchronního zpracování napříč všemi úrovněmi pro optimální výkon1.
Typová bezpečnost
Využití generických typů a rozhraní pro zajištění typové bezpečnosti při komunikaci mezi moduly.
Výhody navrženého řešení
Kompatibilita: Navržený systém je kompatibilní s existující architekturou projektu L.O.N.G.I.N, využívá stávající konektory a respektuje hierarchickou strukturu modulů1.
Škálovatelnost: Kombinace různých komunikačních mechanismů umožňuje snadné rozšíření systému o nové moduly a funkcionality1.
Výkonnost: Využití rychlých mechanismů (EventBus, sdílený stav) pro nižší úrovně a robustnějších řešení (Message Queue, RESTful API) pro vyšší úrovně zajišťuje optimální výkon i při velkém množství modulů a spojek1.
Flexibilita: Hybridní přístup umožňuje přizpůsobení komunikace specifickým potřebám různých úrovní modulů1.
Tento návrh poskytuje vyvážené řešení, které splňuje požadavky na kompatibilitu, škálovatelnost a výkonnost projektu L.O.N.G.I.N, a zároveň umožňuje efektivní komunikaci mezi velkým množstvím modulů a spojek na různých úrovních.


L.O.N.G.I.N
│
├── Core
│   ├── Modules
│   │   ├── Parts
│   │   ├── Units
│   │   ├── Components
│   │   └── Augments
│   ├── Connectors
│   └── Logs
│
├── UI
│
└── Data
    ├── BaseData.txt
    └── Files

INSTALAČNÍ SKRIPT splňuje všechny požadavky:
Je SPUSTITELNÝ NA WINDOWS 
KONTROLUJE A INSTALUJE ZÁVISLOSTI před instalací 
Vytváří ZÁSTUPCE NA PLOŠE.
Přidává informace pro ODINSTALACI do registru Windows.

Abstract clases and interfaces:

"abstraktní implementace spojky (Connector) pro projekt Longin, která umožní využití
jakýmkoliv modulem s libovolným datovým vstupem a výstupem:

Abstraktní třída BaseConnector:
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Any

# Generické typy pro vstup a výstup
InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')

# Logovací úrovně
class LogLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

# Rozhraní pro logovatelné objekty
class ILoggable(ABC):
    @abstractmethod
    def log(self, message: str, level: LogLevel) -> None:
        pass

    @abstractmethod
    def get_log_history(self) -> list:
        pass

# Rozhraní pro konfigurovatelné objekty
class IConfigurable(ABC):
    @abstractmethod
    def set_config(self, config: dict) -> None:
        pass

    @abstractmethod
    def get_config(self) -> dict:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass

# Abstraktní třída BaseConnector
class BaseConnector(ABC, Generic[InputType, OutputType], ILoggable, IConfigurable):

    def __init__(self):
        self.event_bus = None
        self.log_history = []
        self.config = {}

    @abstractmethod
    def validate_data(self, data: InputType) -> bool:
        pass

    @abstractmethod
    def verify_data(self, data: OutputType) -> bool:
        pass

    @abstractmethod
    def transform_data(self, data: InputType) -> OutputType:
        pass

    def log(self, message: str, level: LogLevel) -> None:
        self.log_history.append({"message": message, "level": level})
        print(f"[{level}] {message}")

    def get_log_history(self) -> list:
        return self.log_history

    def set_config(self, config: dict) -> None:
        if self.validate_config(config):
            self.config = config
        else:
            self.log("Neplatná konfigurace", LogLevel.ERROR)

    def get_config(self) -> dict:
        return self.config

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass

    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def emit_event(self, event_name: str, data: Optional[Any] = None):
        if self.event_bus:
            await self.event_bus.emit(event_name, data)
        else:
            self.log("EventBus není nastaven.", LogLevel.WARNING)

# Příklad implementace hierarchického EventBus
class EventBus:
    def __init__(self):
        self.listeners = {}
        self.parent = None
        self.children = []

    def set_parent(self, parent):
        self.parent = parent
        parent.children.append(self)

    async def on(self, event_name: str, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    async def emit(self, event_name: str, data: Optional[Any] = None):
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                await callback(data)
        
        # Propagace události k rodičovskému EventBus
        if self.parent:
            await self.parent.emit(event_name, data)

        # Propagace události k potomkům EventBus
        for child in self.children:
            await child.emit(event_name, data)",

"DETAILNÍ NÁVRH hierarchie ABS a INT tříd pro všechny typy modulů v systému L.O.N.G.I.N
1. Základní ABS třída pro všechny moduly
typescript
abstract class BaseModule {
    protected eventBus: EventBus;

    constructor(eventBus: EventBus) {
        this.eventBus = eventBus;
    }

    abstract init(): Promise<void>;
    abstract process(data: any): Promise<any>;
    abstract shutdown(): Promise<void>;
    abstract getStatus(): ModuleStatus;
}
2. INT pro různé stupně modulů
2.1. IPart
typescript
interface IPart extends BaseModule {
    connectToUnit(): Promise<void>;
    validateInput(data: any): boolean;
    transformOutput(data: any): any;
}
2.2. IUnit
typescript
interface IUnit extends BaseModule {
    connectToComponent(): Promise<void>;
    getParts(): IPart[];
    addPart(part: IPart): void;
    removePart(partId: string): void;
}
2.3. IComponent
typescript
interface IComponent extends BaseModule {
    connectToAugment(): Promise<void>;
    getUnits(): IUnit[];
    addUnit(unit: IUnit): void;
    removeUnit(unitId: string): void;
    processData(data: any): Promise<any>;
}
2.4. IAugment
typescript
interface IAugment extends BaseModule {
    connectToCore(): Promise<void>;
    getComponents(): IComponent[];
    addComponent(component: IComponent): void;
    removeComponent(componentId: string): void;
    executeTask(task: Task): Promise<TaskResult>;
}
3. Specializované INT pro konkrétní typy modulů
3.1. IScanner
typescript
interface IScanner extends IPart {
    scan(url: string): Promise<ScanResult>;
    setFilters(filters: ScanFilter[]): void;
    getSupportedElementTypes(): ElementType[];
}
3.2. IFileStorage
typescript
interface IFileStorage extends IPart {
    saveFile(fileData: Buffer, path: string): Promise<void>;
    readFile(path: string): Promise<Buffer>;
    createFolder(path: string): Promise<void>;
    listFiles(path: string): Promise<string[]>;
}
3.3. IDataProcessor
typescript
interface IDataProcessor extends IUnit {
    processData(data: any): Promise<ProcessedData>;
    addDataTransformer(transformer: DataTransformer): void;
    removeDataTransformer(transformerId: string): void;
}
3.4. IUIComponent
typescript
interface IUIComponent extends IComponent {
    render(): Promise<void>;
    addTab(tab: Tab): void;
    removeTab(tabId: string): void;
    pinTab(tabId: string): void;
    unpinTab(tabId: string): void;
    getPinnedTabs(): Tab[];
}
3.5. IAIAssistant
typescript
interface IAIAssistant extends IAugment {
    generateResponse(prompt: string): Promise<string>;
    setModel(model: AIModel): void;
    getAvailableModels(): AIModel[];
    optimizePrompt(prompt: string): string;
}
4. ABS třídy pro implementaci základní funkcionality
4.1. AbstractPart
typescript
abstract class AbstractPart implements IPart {
    // Implementace společných metod pro všechny Parts
}
4.2. AbstractUnit
typescript
abstract class AbstractUnit implements IUnit {
    // Implementace společných metod pro všechny Units
}
4.3. AbstractComponent
typescript
abstract class AbstractComponent implements IComponent {
    // Implementace společných metod pro všechny Components
}
4.4. AbstractAugment
typescript
abstract class AbstractAugment implements IAugment {
    // Implementace společných metod pro všechny Augments
}
5. Pomocné INT pro OPTIMALIZACI a rozšiřitelnost
5.1. ILoggable
typescript
interface ILoggable {
    log(message: string, level: LogLevel): void;
    getLogHistory(): LogEntry[];
}
5.2. IConfigurable
typescript
interface IConfigurable {
    setConfig(config: ModuleConfig): void;
    getConfig(): ModuleConfig;
    validateConfig(config: ModuleConfig): boolean;
}
5.3. IVersionable
typescript
interface IVersionable {
    getVersion(): string;
    isCompatibleWith(version: string): boolean;
    upgrade(newVersion: string): Promise<void>;
}
Tento DETAILNÍ NÁVRH hierarchie ABS a INT tříd poskytuje ROBUSTNÍ a FLEXIBILNÍ základ pro implementaci všech typů modulů v systému L.O.N.G.I.N. Struktura umožňuje:
SNADNÉ ROZŠÍŘENÍ o nové typy modulů
KONZISTENTNÍ IMPLEMENTACI základních funkcí napříč všemi moduly
EFEKTIVNÍ KOMUNIKACI mezi různými úrovněmi modulů
OPTIMALIZACI výkonu díky možnosti implementace obecných technik na úrovni ABS tříd
TYPOVOU BEZPEČNOST při vývoji a integraci nových modulů
Při implementaci konkrétních modulů je třeba dbát na DODRŽOVÁNÍ této hierarchie a využívání SPRÁVNÝCH INTERFACES pro zajištění KOMPATIBILITY a ŠKÁLOVATELNOSTI celého systému.".
