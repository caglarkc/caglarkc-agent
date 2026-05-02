---
name: approval-flow-orchestration
description: Planner AI için — HITL onay akışının tüm adımlarını koordine etmek; plan sunumu, bekleme, onay/ret işleme ve devam etme.
---

## Purpose

Onay akışı birden fazla adımdan oluşur — her adım doğru sırada yapılmalı.
"Plan gönderildi mi? Onay alındı mı? Sprint başladı mı?" sorularının cevabı netleşir.
Orchestration, akış adımlarının kaybolmamasını sağlar.

---

## When to Apply

- `src/core/approval_orchestrator.py` yazılırken
- Planner → HITL → dispatcher akışı implemente edilirken
- Onay kanalı (CLI, Telegram) entegre edilirken

---

## Rules

- Onay akışı: `plan_ready → notified → waiting → approved/rejected`.
- Her adım loglanır.
- Onay timeout'u ayrı task olarak izlenir.
- Ret: revizyon döngüsüne girer (max 3 kez).
- 3 ret: kullanıcıya "sıfırdan başlayalım mı?" sorulur.

---

## Guidelines

```python
class ApprovalOrchestrator:
    def __init__(
        self,
        notifier: NotificationService,
        compiled_graph,
        repo: ProjectRepository,
    ):
        self._notifier = notifier
        self._graph = compiled_graph
        self._repo = repo
        self._approval_event = asyncio.Event()
        self._approval_result: dict | None = None
    
    async def request_approval(
        self,
        project_id: str,
        sprint_id: str,
        plan_summary: str,
    ) -> bool:
        # 1. Planı bildir
        await self._notifier.send_approval_request(plan_summary, sprint_id)
        logger.info(f"Onay isteği gönderildi: {sprint_id}")
        
        # 2. Timeout ile bekle
        approved = await wait_for_approval_with_timeout(
            project_id=project_id,
            approval_event=self._approval_event,
            notification_service=self._notifier,
        )
        
        if not approved:
            await self._handle_timeout(project_id, sprint_id)
            return False
        
        # 3. Onay/ret işle
        result = self._approval_result or {}
        if result.get("approved"):
            await self._continue_sprint(project_id)
            return True
        else:
            await self._handle_rejection(
                project_id, sprint_id, result.get("reason", "")
            )
            return False
    
    def set_approval_result(self, approved: bool, reason: str = "") -> None:
        self._approval_result = {"approved": approved, "reason": reason}
        self._approval_event.set()
    
    async def _continue_sprint(self, project_id: str) -> None:
        config = get_thread_config(project_id)
        await self._graph.aupdate_state(
            config, {"approval_status": "approved"}
        )
        await self._graph.ainvoke(None, config=config)
```

---

## References

- `interrupt-before-node-skill/SKILL.md` — HITL
- `approval-timeout-handling-skill/SKILL.md` — timeout
- `notification-abstraction-skill/SKILL.md` — bildirim
