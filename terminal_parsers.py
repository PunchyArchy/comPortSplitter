""" Парсеры для известных весовых терминалов """

def parse_data_cas(data):
    """ Парсер для CAS cl-200"""
    data_str = data.decode()
    data_els = data_str.split(',')
    data_kg = data_els[3]
    data_kg_els = data_kg.split(' ')
    kg = data_kg_els[0]
    return kg
