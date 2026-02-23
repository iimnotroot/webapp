import socket
import sys

def validate_args(args: list[str]):
    if len(args) != 2:
        print("usage: server-web-app.py <port>")
        exit(1)
    try:
        int(args[1])
    except ValueError:
        print("error: port must be a number")
        exit(1)
def main():
    args: list[str] = sys.argv
    validate_args(args)
    port: int = int(args[1])

    responseOK = "HTTP/1.1 200 OK\r\n\r\n" \
               + ("<html> "
                  "<body> "
                  "<h1> Hello World </h1> "
                  "<p> El recurso pedido es: {recurso} </p>"
                  "<p> La direccion del usuario es: {direccion} </p>"
                  "<img src=\"https://r-charts.com/es/miscelanea/procesamiento-imagenes-magick_files/figure-html/importar-imagen-r.png\""
                  "width=\"500\" height=\"500\" style=\"TOP:455px;LEFT:500px\">"
                  "<link rel=\"icon\" type=\"image/x-icon\" href=\"favicon.ico\">"
                  "</body>"
                  "</html>") \
               + "\r\n"
    response404= "HTTP/1.1 404 NOT FOUND\r\n"
    responseredirect = (
        "HTTP/1.1 302 Found\r\n"
        "Location: http://gsyc.es\r\n"
        "Conection; close\r\n"
        "\r\n"
    )


    mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mysocket.bind(('0.0.0.0', port))

    mysocket.listen(5)

    while True:
        print("Waiting for connections...\n")
        (recvSocket, address) = mysocket.accept()
        print("HTTP request received:\n")
        print("Petition received from: " + str(address) + "\n")
        received = recvSocket.recv(2048)
        received_str = received.decode('utf-8')
        print("Headers from GET petition:")
        print(received_str)
        petition = received.split()
        dict = petition[1].decode("utf-8")

        if dict != "/" and dict != "/redirect":
            response = response404
        elif dict == "/redirect":
            response = responseredirect
        else:
            response = responseOK.format(recurso=dict, direccion=str(address))

        recvSocket.send(response.encode('utf-8'))
        recvSocket.close()


if __name__ == "__main__":
    main()