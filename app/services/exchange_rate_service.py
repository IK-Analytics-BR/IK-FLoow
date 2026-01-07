import os
import logging
from datetime import date, datetime
from typing import Iterable, Optional

import requests

from database import get_db
from utils.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Serviço de integração com ExchangeRatesAPI.io e cache em banco de dados."""

    def __init__(self):
        cfg = ConfigManager().get_config('exchange_rates') or {}
        self.enabled: bool = bool(cfg.get('enabled', True))
        self.base_url: str = cfg.get('base_url', 'https://api.exchangeratesapi.io/v1')
        self.api_key: str = cfg.get('api_key') or os.environ.get('EXCHANGE_RATES_API_KEY', '')
        self.base_currency: str = cfg.get('base_currency', 'BRL').upper()
        # Lista padrão de moedas alvo para job diário
        self.default_symbols: list[str] = [c.upper() for c in cfg.get('default_symbols', ['USD', 'EUR'])]

    # ========================
    # Métodos públicos
    # ========================

    def get_rate(self, rate_date: Optional[date], target_currency: str) -> float:
        """Retorna a taxa de câmbio (base -> target) para a data informada.

        - Se existir em exchange_rates, usa o valor do banco.
        - Caso contrário, consulta ExchangeRatesAPI.io, grava e retorna.
        """
        if not self.enabled:
            raise RuntimeError('Serviço de câmbio está desabilitado nas configurações.')

        if not self.api_key:
            raise RuntimeError('API key do ExchangeRatesAPI.io não configurada. Defina EXCHANGE_RATES_API_KEY ou app/config/exchange_rates.json.')

        if rate_date is None:
            rate_date = date.today()
        if isinstance(rate_date, str):
            rate_date = datetime.strptime(rate_date, '%Y-%m-%d').date()

        target_currency = target_currency.upper()
        base = self.base_currency

        db = get_db()
        # 1) Tentar no banco
        row = db.fetch_one(
            """
            SELECT rate
            FROM exchange_rates
            WHERE rate_date = %s
              AND base_currency_code = %s
              AND target_currency_code = %s
            """,
            (rate_date, base, target_currency),
        )
        if row and row.get('rate') is not None:
            return float(row['rate'])

        # 2) Buscar na API e gravar
        rates = self._fetch_from_api(rate_date, symbols=[target_currency])
        if target_currency not in rates:
            raise RuntimeError(f"API não retornou taxa para moeda {target_currency} na data {rate_date}.")

        rate_value = float(rates[target_currency])

        insert_sql = (
            "INSERT INTO exchange_rates (rate_date, base_currency_code, target_currency_code, rate, source) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE rate = VALUES(rate), source = VALUES(source)"
        )
        db.execute(insert_sql, (rate_date, base, target_currency, rate_value, 'ExchangeRatesAPI.io'))

        return rate_value

    def update_daily_rates(self, rate_date: Optional[date] = None, target_currencies: Optional[Iterable[str]] = None) -> dict:
        """Atualiza/insere taxas de câmbio para uma lista de moedas em uma data.

        Se target_currencies for None, usa currencies ativas no banco (exceto base) ou default_symbols.
        """
        if not self.enabled:
            return {'success': False, 'message': 'Serviço de câmbio desabilitado.'}

        if not self.api_key:
            return {'success': False, 'message': 'API key do ExchangeRatesAPI.io não configurada.'}

        if rate_date is None:
            rate_date = date.today()
        if isinstance(rate_date, str):
            rate_date = datetime.strptime(rate_date, '%Y-%m-%d').date()

        db = get_db()
        base = self.base_currency

        # Descobrir moedas alvo
        symbols: list[str]
        if target_currencies:
            symbols = [c.upper() for c in target_currencies if c]
        else:
            rows = db.fetch_all(
                """
                SELECT code
                FROM currencies
                WHERE active = 1
                  AND code <> %s
                ORDER BY code
                """,
                (base,),
            )
            if rows:
                symbols = [r['code'].upper() for r in rows]
            else:
                symbols = [c.upper() for c in self.default_symbols if c.upper() != base]

        if not symbols:
            return {'success': False, 'message': 'Nenhuma moeda alvo configurada para atualização.'}

        # Evitar chamadas repetidas à API: buscar apenas moedas que ainda não têm taxa gravada para esta data
        placeholders = ",".join(["%s"] * len(symbols))
        params = [rate_date, base] + symbols
        existing_rows = db.fetch_all(
            f"""
            SELECT target_currency_code
            FROM exchange_rates
            WHERE rate_date = %s
              AND base_currency_code = %s
              AND target_currency_code IN ({placeholders})
            """,
            tuple(params),
        )
        existing_codes = {row['target_currency_code'].upper() for row in existing_rows}

        symbols_to_fetch = [code for code in symbols if code.upper() not in existing_codes]

        if not symbols_to_fetch:
            return {
                'success': True,
                'message': f'Taxas já existentes para {len(symbols)} moeda(s) na data {rate_date}, nenhuma chamada à API foi necessária.',
                'count': 0,
                'date': rate_date.isoformat(),
                'base_currency': base,
            }

        rates = self._fetch_from_api(rate_date, symbols=symbols_to_fetch)

        inserted = 0
        for code in symbols_to_fetch:
            if code not in rates:
                logger.warning("Sem taxa para %s em %s", code, rate_date)
                continue
            rate_value = float(rates[code])
            insert_sql = (
                "INSERT INTO exchange_rates (rate_date, base_currency_code, target_currency_code, rate, source) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE rate = VALUES(rate), source = VALUES(source)"
            )
            db.execute(insert_sql, (rate_date, base, code, rate_value, 'ExchangeRatesAPI.io'))
            inserted += 1

        return {
            'success': True,
            'message': f'Taxas atualizadas para {inserted} moeda(s) na data {rate_date}.',
            'count': inserted,
            'date': rate_date.isoformat(),
            'base_currency': base,
        }

    # ========================
    # Métodos internos
    # ========================

    def _fetch_from_api(self, rate_date: date, symbols: Iterable[str]) -> dict:
        """Consulta a API ExchangeRatesAPI.io e retorna taxas com base na moeda
        configurada (por exemplo, BRL), mesmo que a API use base fixa (ex.: EUR).

        Estratégia para o plano gratuito:
        - A API normalmente usa EUR como base padrão no plano free.
        - Pedimos sempre as cotações de EUR para a moeda base (ex.: BRL) e para
          todas as moedas de interesse.
        - Convertendo: se 1 EUR = X BRL e 1 EUR = Y USD, então 1 BRL = (Y / X) USD.

        O dict retornado é sempre do tipo:
            { 'USD': taxa_de_1_base_para_USD, 'ARS': ..., ... }
        onde "base" é self.base_currency (BRL por padrão).
        """
        base = self.base_currency.upper()

        # Conjunto de moedas alvo (sem a base, pois não faz sentido 1 BRL -> BRL)
        target_codes = {s.upper() for s in symbols if s}
        target_codes.discard(base)

        # Precisamos que a API retorne SEMPRE a moeda base + todos os alvos
        api_symbols = set(target_codes)
        api_symbols.add(base)

        symbols_param = ",".join(sorted(api_symbols)) if api_symbols else None

        # Endpoint por data específica (YYYY-MM-DD) ou latest
        today = date.today()
        if rate_date == today:
            path = 'latest'
        else:
            path = rate_date.strftime('%Y-%m-%d')

        url = f"{self.base_url.rstrip('/')}/{path}"

        # No plano gratuito, a base real da API costuma ser fixa (ex.: EUR).
        # Por isso, NÃO enviamos o parâmetro 'base' aqui; usamos apenas 'access_key'
        # e 'symbols', e depois convertemos para base BRL.
        params = {
            'access_key': self.api_key,
        }
        if symbols_param:
            params['symbols'] = symbols_param

        logger.info("[FX] Chamando ExchangeRatesAPI.io: %s params=%s", url, params)

        resp = requests.get(url, params=params, timeout=10)
        try:
            data = resp.json()
        except Exception:
            data = None

        if resp.status_code != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Falha ao consultar ExchangeRatesAPI.io (HTTP {resp.status_code}).")

        # API atual normalmente retorna {'success': bool, 'error': {...}} em caso de erro lógico
        if data.get('success') is False:
            error_info = data.get('error') or {}
            raise RuntimeError(f"Erro da API ExchangeRatesAPI.io: {error_info}")

        api_rates = data.get('rates')
        if not isinstance(api_rates, dict):
            raise RuntimeError('Resposta da API não contém campo "rates" válido.')

        if base not in api_rates:
            raise RuntimeError(f"API não retornou a moeda base {base} em 'rates'.")

        # Conversão: partindo das taxas EUR->X (ou outra base fixa da API),
        # calculamos taxas base->target.
        base_factor = float(api_rates[base])
        if base_factor == 0:
            raise RuntimeError(f"Taxa da moeda base {base} retornou 0, impossível converter.")

        result: dict[str, float] = {}
        for code in target_codes:
            if code not in api_rates:
                # Se a API não retornou esta moeda, apenas pula; o chamador decide o que fazer.
                logger.warning("[FX] API não retornou taxa para %s na data %s", code, rate_date)
                continue
            target_factor = float(api_rates[code])
            # 1 base -> target
            rate_base_to_target = target_factor / base_factor
            result[code] = rate_base_to_target

        return result
