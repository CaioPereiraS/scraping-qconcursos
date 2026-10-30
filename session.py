import os
from playwright.sync_api import sync_playwright, Browser, Page

from config import Config


class SessaoQConcursos:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._playwright = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=False,
            slow_mo=self.cfg.slow_mo_ms,
        )
        context = self.browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        self.page = context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()

    # ============================================================
    # Login
    # ============================================================

    def login(self):
        assert self.page
        print("→ Fazendo login no QConcursos...")
        self.page.goto("https://www.qconcursos.com/conta/entrar", wait_until="domcontentloaded")

        self.page.locator("#login_email").fill(self.cfg.qc_email)
        self.page.locator("#login_password").fill(self.cfg.qc_senha)

        self.page.locator("[name='commit']").click()
        self.page.wait_for_timeout(5000)
        print("   ✓ Login OK")

    # ============================================================
    # Filtro (último usado)
    # ============================================================

    def ir_para_questoes(self):
        assert self.page
        self.page.goto(
            "https://www.qconcursos.com/questoes-de-concursos/questoes",
            wait_until="domcontentloaded",
        )
        print("→ Aplicando último filtro usado...")
        self.page.locator(".js-apply-last-filter-btn").click()
        self.page.wait_for_timeout(5000)
        self.page.wait_for_selector(".q-questions-list", timeout=10_000)
        print("   ✓ Filtro aplicado")

    # ============================================================
    # Responder todas as questões da página
    # ============================================================

    def revelar_respostas_da_pagina(self):
        """
        Clica em "A" (só pra liberar o gabarito) e depois clica em responder
        em todas as questões da página. Comportamento idêntico ao bot antigo.
        """
        assert self.page

        itens = self.page.locator(".q-question-item")
        total = itens.count()
        print(f"→ Revelando gabarito de {total} questões...")

        # 1. Clica na alternativa A de cada questão (pra liberar botão responder)
        for i in range(total):
            try:
                item = itens.nth(i)
                item.locator(".js-choose-alternative").first.click(timeout=5_000)
            except Exception:
                continue

        # 2. Expande texto associado (se houver)
        for i in range(total):
            try:
                item = itens.nth(i)
                body = item.locator(".q-question-body")
                link = body.locator(".q-link")
                if link.count() > 0:
                    link.first.click(timeout=3_000)
            except Exception:
                continue

        # 3. Clica em "Responder" em cada questão
        botoes = self.page.locator(".js-answer-btn")
        for i in range(botoes.count()):
            try:
                botoes.nth(i).click(timeout=5_000)
            except Exception:
                continue

    # ============================================================
    # Próxima página
    # ============================================================

    def ir_para_proxima_pagina(self) -> bool:
        """Retorna True se conseguiu avançar, False se não há mais páginas."""
        assert self.page
        try:
            botao = self.page.locator(".q-next")
            if botao.count() == 0:
                return False
            if not botao.first.is_enabled():
                return False
            botao.first.click(timeout=10_000)
            self.page.wait_for_load_state("networkidle", timeout=30_000)
            return True
        except Exception:
            return False