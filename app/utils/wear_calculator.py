"""
Módulo para cálculo de desgaste e vida útil de equipamentos e componentes.
Implementa o modelo de desgaste conforme especificações do CMMS.

Antes da solicitação: caso já tenha na versão atual, avance para a próxima.
"""

class WearCalculator:
    """
    Calculadora de desgaste e vida útil para equipamentos e componentes.
    
    Fórmula de cálculo:
    Vida_ajustada = Vida_base × (Horas_padrão / Horas_reais) ÷ (k_intensidade × k_ambiente)
    Desgaste% = Horas_acumuladas / Vida_ajustada
    """
    
    @staticmethod
    def calculate_adjusted_life(base_life_hours, standard_hours_day, real_hours_day, k_intensity, k_environment):
        """
        Calcula a vida útil ajustada com base nos parâmetros de uso.
        
        Args:
            base_life_hours (int): Vida útil base em horas
            standard_hours_day (float): Horas padrão por dia (referência)
            real_hours_day (float): Horas reais por dia do cliente
            k_intensity (float): Fator de intensidade (1.0=leve, 1.1-1.2=médio, 1.3-1.5=pesado)
            k_environment (float): Fator de ambiente (1.0=limpo, 1.1=poeira, 1.2=químicos, 1.3=alta temp.)
            
        Returns:
            int: Vida útil ajustada em horas
        """
        # Validar parâmetros
        if not all([base_life_hours, standard_hours_day, real_hours_day, k_intensity, k_environment]):
            return None
        
        if real_hours_day <= 0 or standard_hours_day <= 0:
            return None
        
        # Aplicar a fórmula
        hours_ratio = standard_hours_day / real_hours_day
        k_factor = k_intensity * k_environment
        
        adjusted_life = base_life_hours * hours_ratio / k_factor
        
        # Arredondar para o inteiro mais próximo
        return int(round(adjusted_life))
    
    @staticmethod
    def calculate_wear_percentage(accumulated_hours, adjusted_life_hours):
        """
        Calcula o percentual de desgaste com base nas horas acumuladas e vida útil ajustada.
        
        Args:
            accumulated_hours (int): Horas acumuladas de operação
            adjusted_life_hours (int): Vida útil ajustada em horas
            
        Returns:
            float: Percentual de desgaste (0-100)
        """
        # Validar parâmetros
        if not adjusted_life_hours or adjusted_life_hours <= 0:
            return None
        
        # Aplicar a fórmula
        wear_percentage = (accumulated_hours / adjusted_life_hours) * 100
        
        # Limitar a 100%
        return min(round(wear_percentage, 2), 100.0)
    
    @staticmethod
    def get_wear_status(wear_percentage):
        """
        Retorna o status de desgaste com base no percentual.
        
        Args:
            wear_percentage (float): Percentual de desgaste
            
        Returns:
            str: Status de desgaste ('normal', 'warning', 'critical')
        """
        if wear_percentage is None:
            return 'unknown'
        
        if wear_percentage >= 100:
            return 'critical'
        elif wear_percentage >= 80:
            return 'warning'
        else:
            return 'normal'
    
    @staticmethod
    def get_environment_factor(environment_type):
        """
        Retorna o fator de ambiente com base no tipo.
        
        Args:
            environment_type (str): Tipo de ambiente ('clean', 'dust', 'chemical', 'high_temp')
            
        Returns:
            float: Fator de ambiente
        """
        factors = {
            'clean': 1.0,
            'dust': 1.1,
            'chemical': 1.2,
            'high_temp': 1.3
        }
        
        return factors.get(environment_type, 1.0)
    
    @staticmethod
    def get_intensity_factor(intensity_level):
        """
        Retorna o fator de intensidade com base no nível.
        
        Args:
            intensity_level (str): Nível de intensidade ('light', 'medium', 'heavy')
            
        Returns:
            float: Fator de intensidade
        """
        factors = {
            'light': 1.0,
            'medium': 1.2,
            'heavy': 1.5
        }
        
        return factors.get(intensity_level, 1.0)
    
    @staticmethod
    def should_generate_alert(wear_percentage):
        """
        Verifica se deve gerar um alerta com base no percentual de desgaste.
        
        Args:
            wear_percentage (float): Percentual de desgaste
            
        Returns:
            tuple: (bool, str) - Se deve gerar alerta e o tipo de alerta
        """
        if wear_percentage is None:
            return (False, None)
        
        if wear_percentage >= 100:
            return (True, 'wear_100')
        elif wear_percentage >= 80:
            return (True, 'wear_80')
        
        return (False, None)
    
    @staticmethod
    def should_generate_maintenance(wear_percentage, preventive_percentage):
        """
        Verifica se deve gerar uma manutenção preventiva com base no percentual de desgaste.
        
        Args:
            wear_percentage (float): Percentual de desgaste
            preventive_percentage (int): Percentual para manutenção preventiva
            
        Returns:
            bool: Se deve gerar manutenção preventiva
        """
        if wear_percentage is None or preventive_percentage is None:
            return False
        
        return wear_percentage >= preventive_percentage
