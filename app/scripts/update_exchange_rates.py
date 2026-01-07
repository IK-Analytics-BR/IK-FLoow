import os
import sys
from datetime import datetime, date, timedelta

# Garantir que o diretório app esteja no sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from services.exchange_rate_service import ExchangeRateService


def main():
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except ValueError:
            print('Data inválida. Use o formato YYYY-MM-DD.')
            sys.exit(1)
    else:
        # Por padrão, buscar sempre a cotação de FECHAMENTO DO ÚLTIMO DIA ÚTIL
        today = date.today()
        # weekday(): Monday=0, Sunday=6
        if today.weekday() == 0:
            # Segunda-feira -> usar sexta-feira (3 dias antes)
            target_date = today - timedelta(days=3)
        else:
            # Demais dias -> usar ontem
            target_date = today - timedelta(days=1)

    service = ExchangeRateService()

    try:
        result = service.update_daily_rates(rate_date=target_date)
        print(result.get('message'))
    except Exception as e:
        print(f"Erro ao atualizar taxas de câmbio: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
