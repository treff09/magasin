import psycopg2
from decouple import config

try:
    # Print the connection parameters to check if they are correct
    print(f"Attempting to connect with the following parameters:\n"
          f"dbname={config('NAME')}\n"
          f"user={config('USER')}\n"
          f"password={config('PASSWORD')}\n"
          f"host={config('HOST')}\n"
          f"port={config('PORT')}")

    connection = psycopg2.connect(
        dbname=config('NAME'),
        user=config('USER'),
        password=config('PASSWORD'),
        host=config('HOST'),
        port=config('PORT')
    )
    print("Connexion réussie")

except psycopg2.OperationalError as e:
    print(f"Erreur opérationnelle de connexion : {e}")

except UnicodeDecodeError as e:
    print(f"Erreur d'encodage : {e}")

except Exception as e:
    print(f"Erreur de connexion : {e}")

finally:
    if 'connection' in locals():
        connection.close()