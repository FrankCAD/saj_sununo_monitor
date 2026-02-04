var xmlhttp_par;
function display_par()
{
if(xmlhttp_par.readyState==4&& xmlhttp_par.status==200)
{
var xmlDoc=xmlhttp_par.responseXML.documentElement;

with(document){
getElementById("v-grid").value=xmlDoc.getElementsByTagName("v-grid")[0].childNodes[0].nodeValue+" V";
getElementById("i-grid").value=xmlDoc.getElementsByTagName("i-grid")[0].childNodes[0].nodeValue+" A";
getElementById("f-grid").value=xmlDoc.getElementsByTagName("f-grid")[0].childNodes[0].nodeValue+" Hz";
getElementById("p-ac").value=xmlDoc.getElementsByTagName("p-ac")[0].childNodes[0].nodeValue+" W";
getElementById("temp").value=xmlDoc.getElementsByTagName("temp")[0].childNodes[0].nodeValue+" ℃";
getElementById("e-today").value=xmlDoc.getElementsByTagName("e-today")[0].childNodes[0].nodeValue+" kWh";
getElementById("t-today").value=xmlDoc.getElementsByTagName("t-today")[0].childNodes[0].nodeValue+" h";
getElementById("e-total").value=xmlDoc.getElementsByTagName("e-total")[0].childNodes[0].nodeValue+" kWh";
getElementById("t-total").value=xmlDoc.getElementsByTagName("t-total")[0].childNodes[0].nodeValue+" h";
getElementById("CO2").value=xmlDoc.getElementsByTagName("CO2")[0].childNodes[0].nodeValue+" kg";
getElementById("v-pv1").value=xmlDoc.getElementsByTagName("v-pv1")[0].childNodes[0].nodeValue+" V";
getElementById("i-pv1").value=xmlDoc.getElementsByTagName("i-pv1")[0].childNodes[0].nodeValue+" A";
getElementById("v-pv2").value=xmlDoc.getElementsByTagName("v-pv2")[0].childNodes[0].nodeValue;
getElementById("i-pv2").value=xmlDoc.getElementsByTagName("i-pv2")[0].childNodes[0].nodeValue;
getElementById("v-bus").value=xmlDoc.getElementsByTagName("v-bus")[0].childNodes[0].nodeValue+" V";
getElementById("Inverter-Stare").value=xmlDoc.getElementsByTagName("state")[0].childNodes[0].nodeValue;
}
}
}
