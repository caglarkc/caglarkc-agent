# Son Test — Tespit Edilen Kritik Sorunlar

## Bug 1: `KeyError: 'project_id'` — planner.py:112

**Hata logu:**
```
KeyError: 'project_id'
File "src/graph/nodes/planner.py", line 112, in _manager_planner_node
    project_id = state["project_id"]
```

**Sebep:** `graph_manager.py` bazı durumlarda `aupdate_state` + `Command(goto="planner")` çağırıyor. Eğer checkpoint state'i boşsa ya da `project_id` channel'ı henüz initialize edilmemişse, planner node `state["project_id"]` ile KeyError fırlatıyor.

**Fix:** `state["project_id"]` → `state.get("project_id")` ile guard ekle; `project_id` yoksa graceful hata döndür.

---

## Bug 2: `InvalidUpdateError: task_description` — LangGraph state çakışması

**Hata logu:**
```
InvalidUpdateError: At key 'task_description': Can receive only one value per step.
```

**Sebep:** Eski kod `Command(goto="planner", update=state_update)` ile `ainvoke` çağırıyordu. Bu durumda hem checkpoint state hem de `update` aynı adımda `task_description`'a değer yazmaya çalışıyordu. *(Bu kod `aupdate_state + Command(goto="planner")` patterni ile düzeltildi, ancak aynı risk başka alanlarda da olabilir.)*

**Durum:** `graph_manager.py` güncel versiyonunda `aupdate_state` + `ainvoke(Command(goto="planner"))` kullanılıyor — düzeltme uygulanmış. Ama `project_id` KeyError bu değişikliğin yan etkisi.

---

## Bug 3: `messages` listesi sınırsız büyüyor

**Tespit:** `state_snapshot.json`'da bazı projelerde 27 tane `"planner completed"` mesajı birikmiş.

**Sebep:** `state.py`'da `messages: Annotated[list[str], operator.add]`. Her planner çağrısında `["planner completed"]` ekleniyor. Uzun süreli kullanımda state şişiyor.

**Fix:** Reducer'ı `lambda a, b: (a + b)[-100:]` yap — son 100 mesajı tut.

**İkincil sorun:** `graph_manager.py`'da `_resume_graph` ve `_stop_graph` mesajları `[*snapshot.values.get("messages", []), "yeni mesaj"]` şeklinde gönderiyor. `operator.add` reducer ile bu mevcut mesajları **iki kez** ekliyor (duplication). Fix ile birlikte bu pattern da düzeltilmeli.

---

## Bug 4: "Deneme Proje" — `src/Main.java` hiç yazılmadı

**Tespit:** Plan `awaiting_approval` durumunda kaldı. `projects/Deneme Proje/` altında sadece `.meta/plan.json` var, `src/Main.java` yok.

**Sebep:** Test, `/approve <approval_id>` adımına geçmeden kesildi. Worker execution hiç başlamadı.

**Durum:** Sistemin hatası değil — test yarım kaldı. Execution loop test edilmedi. Execution testi için planı onaylayıp worker çalıştırmak gerekiyor.

---

## Bug 5: Farklı projeler aynı `planning_thread_id` paylaşıyor

**Tespit:** `phase3-contract-0a6307e2`, `phase3-deps-81825cb4`, `phase3-scope-434e0ea0` hepsi `thread-790682087426445d99deaa54198fda5c` paylaşıyor.

**Sebep:** Test scriptleri projeleri sabit bir thread ID ile oluşturuyor. Gerçek kullanımda her proje kendi thread'ini alıyor — bu production bug değil, test setup sorunu.

---

## Öncelik Sırası

| # | Bug | Öncelik | Etki |
|---|-----|---------|------|
| 1 | `project_id` KeyError | Kritik | Yeni mesajlarda crash |
| 2 | `messages` duplication/şişme | Orta | State kirlenmesi |
| 3 | `task_description` çakışması | Düşük | Eski kod — zaten düzeltilmiş |
| 4 | Execution testi eksik | Orta | Test kapsamı yetersiz |
| 5 | Thread ID paylaşımı | Düşük | Sadece test scriptlerinde |
