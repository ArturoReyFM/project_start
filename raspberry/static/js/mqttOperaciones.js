let mqtt;
const port = 9001;
const host = '192.168.0.12';
const reconnectTimeout = 2000;
const nivelMaxTambo = 86 - 19;
const nivelMaxTinaco = 84.5 - 20;

function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  mqtt.subscribe('Nivel_agua/tambo');
  mqtt.subscribe('Nivel_agua/tinaco');
  mqtt.subscribe('notificaciones');
  message = new Paho.MQTT.Message('Servidor web');
  message.destinationName = 'status';
  mqtt.send(message);
}
function onFailure(message) {
  console.log('Conexión al host' + host + ' falló');
  setTimeout(MQTT.connect, reconnectTimeout);
}
function calcularPorcentajeNivel(nivel, componente) {
  if (componente == 'tambo') {
    return (nivel * 100) / nivelMaxTambo;
  } else if (componente == 'tinaco') {
    return (nivel * 100) / nivelMaxTinaco;
  }
}
function onMessageArrived(msg) {
  let inmsg, topic, place;
  [topic, place] = msg.destinationName.split('/');
  if (topic == 'Nivel_agua') {
    inmsg = msg.payloadString;
    nivel = parseFloat(inmsg);

    if (place == 'tambo') {
      nivel = calcularPorcentajeNivel(nivel, 'tambo').toFixed(1);
      dispatch('niveles', { tambo: nivel });
    } else if (place == 'tinaco') {
      nivel = calcularPorcentajeNivel(nivel, 'tinaco').toFixed(1);
      dispatch('niveles', { tinaco: nivel });
    }
  } else if (topic === 'notificaciones') {
    inmsg = msg.payloadString;
    dispatch('notificacion', JSON.parse(inmsg));
  }
}

function MQTTconnect() {
  console.log('connecting to ' + host + ' ' + port);
  const x = Math.floor(Math.random() * 10000);
  const cname = 'orderform-' + x;
  mqtt = new Paho.MQTT.Client(host, port, cname);
  const options = {
    timeout: 3,
    onSuccess: onConnect,
    onFailure: onFailure,
  };
  mqtt.onMessageArrived = onMessageArrived;

  mqtt.connect(options); //connect
}

// Action functions //

function encenderBomba() {
  message = new Paho.MQTT.Message('1');
  message.destinationName = 'Bomba';
  mqtt.send(message);
}

function apagarBomba() {
  message = new Paho.MQTT.Message('0');
  message.destinationName = 'Bomba';
  mqtt.send(message);
}
function modoAutomatico() {
  message = new Paho.MQTT.Message('automatico');
  message.destinationName = 'modo';
  const modoauto = document.getElementById('automatico');
  if (modoauto.checked) {
    document.getElementById('encenderApagarBomba').checked = false;
    mqtt.send(message);
  }
}
function modoSemiautomatico() {
  message = new Paho.MQTT.Message('semiautomatico');
  message.destinationName = 'modo';
  const modosemi = document.getElementById('semi');
  if (modosemi.checked) mqtt.send(message);
}
function modoManual() {
  message = new Paho.MQTT.Message('manual');
  message.destinationName = 'modo';
  const modomanual = document.getElementById('manual');
  if (modomanual.checked) mqtt.send(message);
}

MQTTconnect();

window.addEventListener('mqttEvent', ({ detail } = e) => {
  switch (detail.type) {
    case 'encender':
      encenderBomba();
      break;
    case 'apagar':
      apagarBomba();
      break;
    case 'automatico':
      modoAutomatico();
      break;
    case 'semiautomatico':
      modoSemiautomatico();
      break;
    case 'manual':
      modoManual();
      break;
    default:
      console.log('No ocurrió nada');
      break;
  }
});

function dispatch(name, detail) {
  const mqttEvent = new CustomEvent(name, {
    detail,
    bubbles: true,
    composed: true,
  });
  window.dispatchEvent(mqttEvent);
}
