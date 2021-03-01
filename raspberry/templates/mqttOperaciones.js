class status {
            constructor(){
                this.status = "";
            }
        }
		var mqtt;
		var reconnectTimeout = 2000;
		var host="192.168.0.6"; //change this
        const nivelMaxTambo = 86 - 19;
        const nivelMaxTinaco = 84.5 - 20;
        
		//var host="steve-laptop"; //change this

		//var port=8080
		var port=9001;
		//var port=8881;
        var mensaje;
        
        
		stats = new status();
	 	function onConnect() {
	  // Once a connection has been made, make a subscription and send a message.
	
		console.log("Connected ");
		mqtt.subscribe("Nivel_agua/tambo");
        mqtt.subscribe("Nivel_agua/tinaco");
		message = new Paho.MQTT.Message("Servidor web");
		message.destinationName = "status";
		mqtt.send(message);
	  }
      function onFailure(message){
        console.log("Conexión al host"+host+" falló");
        setTimeout(MQTT.connect,reconnectTimeout);
      }
      function calcularPorcentajeNivel(nivel,componente){
          if (componente == "tambo"){
              return (nivel*100)/nivelMaxTambo;
          }
          else if (componente =="tinaco"){
              return (nivel*100)/nivelMaxTinaco;
          }
      }
      function onMessageArrived(msg){
          if (msg.destinationName.split("/")[0] == "Nivel_agua"){
            inmsg = msg.payloadString;
            nivel = parseFloat(inmsg);

            if (msg.destinationName.split("/")[1]  == "tambo"){
                nivel = calcularPorcentajeNivel(nivel,"tambo").toFixed(1);
                document.getElementById("nivel_tambo").innerHTML = nivel.toString() + "%";

            }
            else if (msg.destinationName.split("/")[1]  == "tinaco"){
                nivel = calcularPorcentajeNivel(nivel,"tinaco").toFixed(1);
                document.getElementById("nivel_tinaco").innerHTML = nivel.toString() + "%";
                //console.log(inmsg);
            }

          }
        
        
         
          
      }
    function encenderBomba(){
        message = new Paho.MQTT.Message("1");
        message.destinationName = "Bomba";
        mqtt.send(message);
        }

    function apagarBomba(){
        message = new Paho.MQTT.Message("0");
		message.destinationName = "Bomba";
        mqtt.send(message);
    }
    function modo_automatico(){
        message = new Paho.MQTT.Message("automatico");
        message.destinationName = "modo";
        var modoauto = document.getElementById("automatico");
        if (modoauto.checked){
            document.getElementById("encenderBomba").disabled = true;
            document.getElementById("apagarBomba").disabled = true;
            mqtt.send(message);
        }
    }
    function modo_semiautomatico(){
        message = new Paho.MQTT.Message("semiautomatico");
        message.destinationName = "modo";
        var modosemi = document.getElementById("semi");
        if (modosemi.checked){
            document.getElementById("encenderBomba").disabled = false;
            document.getElementById("apagarBomba").disabled = false;
            mqtt.send(message);
        }
    }
    function modo_manual(){
        message = new Paho.MQTT.Message("manual");
        message.destinationName = "modo";
        var modomanual = document.getElementById("manual");
        if (modomanual.checked){
            document.getElementById("encenderBomba").disabled = false;
            document.getElementById("apagarBomba").disabled = false;
            mqtt.send(message);
        }
    }
    function desabilitarBotones(){
            document.getElementById("encenderBomba").disabled = true;
            document.getElementById("apagarBomba").disabled = true;
    }

	  function MQTTconnect() {
		console.log("connecting to "+ host +" "+ port);
		var x=Math.floor(Math.random() * 10000); 
		var cname="orderform-"+x;
		mqtt = new Paho.MQTT.Client(host,port,cname);
		//document.write("connecting to "+ host);
		var options = {
	
			timeout: 3,
			onSuccess: onConnect,
            onFailure:onFailure,

		  
		 };
         mqtt.onMessageArrived = onMessageArrived;
		 
		mqtt.connect(options); //connect
		}
	 