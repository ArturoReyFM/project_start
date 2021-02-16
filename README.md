# Comandos de operacion y muestreo

### Verificacion de niveles
```shell
mosquitto_sub -h localhost -t Nivel_agua/tambo 
mosquitto_sub -h localhost -t Nivel_agua/tinaco
```

### Verificacion de conexion
```shell
mosquitto_sub -h localhost -t ips/tinaco
mosquitto_sub -h localhost -t ips/tambo
mosquitto_sub -h localhost -t ips/bomba
```

### Cambiar a modo automatico o manual
```shell
mosquitto_pub -h localhost -t "modo" -m "automatico"
mosquitto_pub -h localhost -t "modo" -m "manual"
```

### Prender y apagar bomba
```shell

mosquitto_pub -h localhost -t Bomba -m "1"
mosquitto_pub -h localhost -t Bomba -m "0"
```

### Estado de todo el sistema
```shell
mosquitto_sub -h localhost -t status
```


