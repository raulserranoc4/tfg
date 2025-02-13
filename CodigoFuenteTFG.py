import re   

# EXPRESIONES REGULARES

decimalNumber = r'[\d.]+'
naturalNumber = r'-?'+decimalNumber

font = r'\S*'

lineFont = r'/('+font+r') ('+decimalNumber+r') Tf\n'
linePos = r'(\d|\s)*?('+naturalNumber+r') ('+naturalNumber+r') (Tm|Td|TD)\n'
lineEvery = r'T\*\n'

regexID = r'(\d+) \d+ obj'
regexReferencia = r'\d+ \d+ R'
regexKids = r'/Kids \[(.*?)\]|/K \[(.*?)\]'
regexParent = r'/Parent (\d+) (.*?)'
regexContent = r'/Contents (\d+ 0 R)'
regexStream = r'stream(.*?)endstream'

regexObject = r'\d+ \d+ obj(?:\n<<[\s\S]*?endobj|\nendobj)'

regexContentReference = r'((?!<<|\[)(.*?)\n|(<<\n.*?>>)\n|((\[.*?\])\n(/|>>)))'
regexReference = r'/(\S+) '+regexContentReference
regexRealContent = r'<<(.*?)>>\nendobj'

regexTexts = r'(/Span|/P|/LBody|/Artifact)(.*?)EMC'

regexTextBegin1 = r'/MCID (\d+)(.*?)(Tj|TJ)'
regexTextBegin2 = r'/BBox(.*?)(Tj|TJ)'

# Expresiones regulares para las líneas de impresión del texto
regexTextContent1 = r'('+lineFont+r')?('+linePos+r')?('+lineEvery+r')?\((.*?)\)Tj'
regexTextContent2 = r'('+lineFont+r')?('+linePos+r')?('+lineEvery+r')?\[(((?<!\\)\((.*?)(?<!\\)\))?(-?(\d|\s)*(?<!\\)\(.*?(?<!\\)\))*)\]TJ'
regexTextContent3 = r'('+lineFont+r')?('+linePos+r')?('+lineEvery+r')?\[?(<(.*?)>(-(\d|\s)*<.*?>)*)\]?T(J|j)'
regexTextContent4 = r'('+lineFont+r')?('+linePos+r')?('+lineEvery+r')?\[-?(\d)\(\w\)\]TJ'



# CLASES

# Clase de objeto del cuerpo del PDF
class Object:
     def __init__(self, content, id):
        self.id = id
        self.content = content
        self.kids = []
        self.contents = ""
        self.printedTexts = []
        self.references = {}


# Clase de la instrucción de imprimir un texto de un PDF
class PrintedText:
    def __init__(self, id, font, size, rowText, text, posX, posY):
        self.id = id
        self.font = font
        self.size = size
        self.rowText = rowText
        self.text = text
        self.posX = posX
        self.posY = posY


# MÉTODOS

# Método que obtiene el id de un objeto
def getID(content):
    line = re.findall(regexID,content)
    return int(line[0])


# Método que obtiene los hijos de un objeto
def getKids(content):
    match = re.search(regexKids, content)
    listIDs =[]

    if match:
            reference = match.group()
            listReferences = re.findall(r'\b(\d+) 0 R\b', reference)
            listIDs = [int(num) for num in listReferences]
    return listIDs


# Método que obtiene la referencia de clave /Contents
def getContents(content):
    match = re.search(regexContent, content)
    if match:
        reference = match.group(1)
        contentsStr = reference.split()[0]
        contentsInt = int(contentsStr)
        return contentsInt


# Método que obtiene las referencias que están el el diccionario de los objetos
def getReferences(content):
    ref_dic = {}
    references = re.findall(regexReference, content, re.DOTALL)
    for ref in references:
        if ref[2] != '':
            ref_dic[ref[0]] = ref[2]
        elif ref[3] != '':
            ref_dic[ref[0]] = ref[3]
        elif ref[5] != '':
            ref_dic[ref[0]] = ref[5]
            #print(ref[5])
    return ref_dic

# Método que decodifica un texto en hexdecimal a texto ascii
def hex_to_ascii(hex_string):
    bytes_object = bytes.fromhex(hex_string)
    ascii_string = bytes_object.decode('latin1')

    ascii_string = ascii_string.replace('\x0c', 'f')
    ascii_string = ascii_string.replace('\r', 'f')
    return ascii_string

# Método que comprueba si hay alún caracter especial y lo cambie en una cadena de texto
def search_special_character(text):
    if text == "f":
            text = "{"
    if text == "g":
            text = "}"
    if text == "n":
            text = "\\"
    if text == "\\003":
            text = "*"
    return text

# Método que comprueba si hay alún caracter especial y lo cambie en una lista de cadenas de texto
def search_spectial_characters(parts):
    if(len(parts) == 1):
        for i in range(len(parts)):
            if parts[i] == "f":
                parts[i] = "{"
            if parts[i] == "g":
                parts[i] = "}"
            if parts[i] == "n":
                parts[i] = "\\"
    return parts                                

# Método que obtiene los textos que se imprimen en un objeto de tipo contenido
def parse_text(obj,string):
    txt = PrintedText
    match1 = re.search(regexTextBegin1, string, re.DOTALL) # Comprueba si coincide con el formato de tecto MCID
    if match1:
        id = match1[1]  # Obtiene el id de la instrucción
        aux_text = string[10:]

        # Encuentra todos los textos que se imprimen dependendiendo de como estén organizadas las cadenas de texto
        list_aux = re.findall(r'('+regexTextContent1+r')|('+regexTextContent2+r')|('+regexTextContent3+r')',aux_text, re.DOTALL)

        # Por cada texto y dependiendo del formato recoge el tipo de fuente, el tamaño, el desplazamiento horizontal y vertical
        # y el texto que se imprime
        for aux in list_aux:
            if aux[0] != '':
                font = aux[2]
                size = (aux[3])
                posX = aux[6]
                posY = aux[7]
                rowText = aux[10]
                text = search_special_character(aux[10])
                txt = PrintedText(id, font, size, rowText, text, posX, posY)
            else:
                if aux[11] != '':
                    font = aux[13]
                    size = (aux[14])
                    posX = aux[17]
                    posY = aux[18]
                    rowText = aux[21]
                    parts = re.findall(r'(?<!\\)\((.*?)(?<!\\)\)', aux[21])
                    parts = search_spectial_characters(parts)
                    text = ''.join(parts)
                    txt = PrintedText(id, font, size, rowText, text, posX, posY)
                else:
                    if aux[26] != '':
                        font = aux[28]
                        size = (aux[29])
                        posX = aux[32]
                        posY = aux[33]
                        rowText = aux[36]
                        parts = re.findall(r'<(.*?)>', aux[36])
                        text_parts = [hex_to_ascii(hex) for hex in parts]
                        text = ''.join(text_parts)
                        txt = PrintedText(id, font, size, rowText, text, posX, posY)

            obj.printedTexts.append(txt) # Añade el texto a imprimir en la lista de textos del objeto

    else:
         match2 = re.search(regexTextBegin2, string, re.DOTALL)
         if match2:
            id = '0'
            aux_text = string[15:]
            # Encuentra todos los textos que se imprimen dependendiendo de como estén organizadas las cadenas de texto
            list_aux = re.findall(r'('+regexTextContent1+r')|('+regexTextContent2+r')|('+regexTextContent3+r')',aux_text, re.DOTALL)

            # Por cada texto y dependiendo del formato recoge el tipo de fuente, el tamaño, el desplazamiento horizontal y vertical
            # y el texto que se imprime
            for aux in list_aux:
                if aux[0] != '':
                    font = aux[2]
                    size = (aux[3])
                    posX = aux[6]
                    posY = aux[7]
                    rowText = aux[10]
                    text = search_special_character(aux[10])
                    txt = PrintedText(id, font, size, rowText, text, posX, posY)
                else:
                    if aux[11] != '':
                        font = aux[13]
                        size = (aux[14])
                        posX = aux[17]
                        posY = aux[18]
                        rowText = aux[21]
                        parts = re.findall(r'(?<!\\)\((.*?)(?<!\\)\)', aux[21])
                        parts = search_spectial_characters(parts)
                        text = ''.join(parts)
                        txt = PrintedText(id, font, size, rowText, text, posX, posY)
                    else:
                        if aux[26] != '':
                            font = aux[28]
                            size = (aux[29])
                            posX = aux[32]
                            posY = aux[33]
                            rowText = aux[36]
                            parts = re.findall(r'<(.*?)>', aux[36])
                            text_parts = [hex_to_ascii(hex) for hex in parts]
                            text = ''.join(text_parts)
                            txt = PrintedText(id, font, size, rowText, text, posX, posY)

                obj.printedTexts.append(txt)    # Añade el texto a imprimir en la lista de textos del objeto
              
# Método que imprme el árbol de estructura desde los objetos de tipo página hasta los objetos de contenido de las páginas
def print_struct_tree(nodo, prefijo='', es_ultimo=True):
    print(prefijo, end='')
    print('└─' if es_ultimo else '├─', end='')
    print(nodo.id, end='')
    print(f' ->{nodo.contents}' if(nodo.contents != None) else '')
 
    prefijo += '   ' if es_ultimo else '│  '
    cantidad_hijos = len(nodo.kids)
    
    for i, hijo in enumerate(nodo.kids):
        es_ultimo = i == cantidad_hijos - 1
        print_struct_tree(hijo, prefijo, es_ultimo)

# Método que imprime el documento PDF entero imprimiendo los textos de todas las páginas
def print_pdf(listContents):
     for obj in listContents:
          previous_height = obj.printedTexts[0].posY
          for text in obj.printedTexts:
                if(text.posY != ''):
                    if (abs(float(text.posY) - float(previous_height)) > 10 and text.posY != '0'):
                        print('\n'+text.text, end='')
                    else:
                        print(text.text, end='')
                    previous_height = text.posY
                else:
                    print(text.text, end='')

          print()
          print()

# Método que imprime los textos de una de las páginas
def print_sheet(obj):
    previous_height = obj.printedTexts[0].posY
    for text in obj.printedTexts:
        if(text.posY != ''):
            if (abs(float(text.posY) - float(previous_height)) > 10 and text.posY != '0'):
                print('\n'+text.text, end='')
            else:
                print(text.text, end='')
            previous_height = text.posY
        else:
             print(text.text, end='')

# Método que enseña los textos que tiene una página e imprime uno que el usuario selecciona
def show_printed_texts(obj):
    print()
    print("Elige un texto con id de los siguientes que quieras imprimir: ")
    print()

    n = 0
    for text in obj.printedTexts:
        if n == 10:
            print(f'[{text.id}]')
            n = 0
        else:
             print(f'[{text.id}]', end=', ')
        n += 1

# Método que imprime los textos de un objeto cuyo id es uno pasado como argumento
def print_text_by_id(id, obj):
    print()
    print(f"El id es {id}")
    for text in obj.printedTexts:
        if text.id == id:
            print(f'Tipo de fuente:\'{text.font}\', Tamaño:\'{text.size}\', Pos horizontal:\'{text.posX}\', Pos Vertical:\'{text.posY}\', Texto:\'{text.text}\'')

# Método que imprime las referencias del diccionario de un objeto
def print_referencias(obj):
    print()
    for clave, valor in obj.references.items():
        print(f"{clave, valor}")
    print()

# Método que modifica el valor de una referencia de un objeto
def modificar_referencia(obj):
    while True:
        print_referencias(obj)

        clave = input("Escriba la clave del valor que quiere cambiar: ")
        if clave in obj.references:
            antiguo_valor = obj.references[clave]
            print(f"\n[{clave} -> {obj.references[clave]}]\n")
            nuevo_valor = input("Escriba el nuevo valor de esta referencia. Ten en cuenta de que puedes estropear el PDF (0 para volver): ")
            if nuevo_valor != '0':

                obj.references[clave] = nuevo_valor

                listCambiosReferences.append([obj, clave, antiguo_valor, nuevo_valor])
                print("Valor cambiado...")
                break
            else:
                break
        else:
            print(f"La clave '{clave}' no existe en el diccionario.")

# Método que modfica el valor de un texto de un objeto
def modificar_texto(id_text, obj):
    for text in obj.printedTexts:
        if text.id == id_text:
            nuevo_valor = input("Inserte el nuevo valor de este texto: ")
            antiguo_valor = text.rowText
            text.text = nuevo_valor

            listCambiosTexts.append([obj, id_text, antiguo_valor, nuevo_valor])
            print("Valor cambiado...")

# Método que modifica el contenido de código del documento PDF pasado
def modificar_pdf():

    new_content = contenido
    for cambio in listCambiosReferences:
        new_content = modificar_pdf_referencias(new_content, cambio)

    for cambio in listCambiosTexts:
        new_content = modificar_pdf_textos(new_content, cambio)         

    return new_content

# Método que modifica las referencias de un objeto en el contenido de código del documento PDF pasado
def modificar_pdf_referencias(content, cambio):
    regexObj = str(cambio[0].id)+r" 0 obj.*?endobj"

    match = re.search(regexObj,content,re.DOTALL)
    if match:
        last_match = match.group()
        regexReference = r'/'+str(cambio[1])+r' '+regexContentReference
        match1 = re.search(regexReference, match.group())
        if match1:
            last_match1 = match1.group()
            new_match1 = match1.group().replace(cambio[2],cambio[3])

        new_match = match.group().replace(last_match1,new_match1)

        new_content = content.replace(last_match,new_match)

    return new_content

# Método que modifica los textos de un objeto en el contenido de código del documento PDF pasado
def modificar_pdf_textos(content, cambio):
    regexObj = str(cambio[0].id)+r" 0 obj.*?endobj"
    new_content = content
    match = re.search(regexObj,content,re.DOTALL)
    if match:
        last_match = match.group()
        regexReference = r'MCID '+str(cambio[1])+r'.*?EMC'
        match1 = re.search(regexReference, match.group(), re.DOTALL)
        if match1:
            last_match1 = match1.group()
            textSearch = cambio[2].replace("(","\(")
            textSearch2 = textSearch.replace(")","\)")
            regexRowText = r'(\('+textSearch2+r'\))(T(j|J))'

            match2 = re.search(regexRowText,match1.group())
            if match2:
                last_match2 = match2.group()
                newText = "("+cambio[3]+")Tj"
                new_match1 = match1.group().replace(last_match2,newText, 1)

                new_match = match.group().replace(last_match1,new_match1)

                new_content = content.replace(last_match,new_match)
            else:
                regexRowText2 = r'(\['+textSearch2+r'\])(T(j|J))'
                match3 = re.search(regexRowText2,match1.group())
                if match3:
                    last_match3 = match3.group()
                    newText = "[("+cambio[3]+")]TJ"
                    new_match1 = match1.group().replace(last_match3,newText, 1)

                    new_match = match.group().replace(last_match1,new_match1)

                    new_content = content.replace(last_match,new_match)
    return new_content

# Método que imprime los hijos de un objeto
def print_kids(obj):
    print()
    if obj.kids == []:
        print("Este objeto no tiene objetos hijos")
    else:
        print("El objeto seleccioado tiene los siguuientes objetos hijos:")
        for kid in obj.kids:
            print(kid.id, end=", ")
        print()
        print()
    return obj.kids

# Método que elimina una referencia a los hijos de un objeto
def delete_kid(obj, kid_id):
    for kid in obj.kids:
        if kid.id == kid_id:
            obj.kids.remove(kid)
            print(f"Objeto con id {kid.id} eliminado...")

# Método que añade una referencia a los hijos de un objeto
def add_kid(obj, kid_id):
    obj.kids.append(listObjects[id-1])
    print(f"Objeto con id {kid_id} añadido...")
    
# Método que gestiona si se quiere añadir, eliminar o ver los hijos de un objeto
def gestionar_hijos(id):
    kids = print_kids(listObjects[id-1])
    if kids == []:
        return
    else:
        show_kids_menú()
        opcion = input("Elija una opción: ")
        if opcion == '0':
            return
        elif opcion == '1':
            new_id = input("Elija un hijo: ")
            if any(kid.id == int(new_id) for kid in kids):
                delete_kid(listObjects[id-1], int(new_id))
            else:
                print("El id no es no hijo de este objeto")
                return
        elif opcion == '2':
            new_id = input("Elija un hijo: ")
            if any(int(new_id) < 2933 and int(new_id) > 0):
                add_kid(listObjects[id-1], int(new_id))
            else:
                print("El id no es válido")
                return
        elif opcion == '3':
            new_id = input("Elija un hijo: ")
            if any(kid.id == int(new_id) for kid in kids):
                gestionar_hijos(int(new_id))
            else:
                print("El id no es no hijo de este objeto")
                return

# Método que muestra el menú de las opcione suqe se pueden realizar con los hijos de un objeto
def show_kids_menú():
    print("1. Eliminar un hijo")
    print("2. Añadir un hijo")
    print("3. Acceder al hijo")
    print("0. Salir")

# Abrir el archivo PDF
file_path = "c:/Users/34629/Documents/UNIVERSIDAD/TFG/decompressedPDF,txt"
try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as archivo:
        contenido = archivo.read()
except UnicodeDecodeError as e:
    print("Error de decodificación Unicode:", e)

# Cargar objetos
listObjects = []
listContents = []
listIntContents = []

listCambiosReferences = []
listCambiosTexts = []


objetos = re.findall(regexObject, contenido)


for objeto in objetos:
    id = getID(objeto)
    newObject = Object(objeto,id)
    listObjects.append(newObject)

# Cargar objetos
for obj in listObjects:
    children = getKids(obj.content) # Cargar ids de los hijos

    obj.contents = getContents(obj.content)
    if obj.contents != None:
        listIntContents.append(obj.contents)


    # Cargar referencias
    obj.references = getReferences(obj.content)

    # Cargar la la lista de objetos hijos de un objeto
    for obj2 in listObjects:
        for child in children:
            if obj2.id == child:
                obj.kids.append(obj2)

    # Cargar la lista de ids de los objetos de tipo contenido
    for n in listIntContents:
        if obj.id == n:
               listContents.append(obj)


# Cargar los textos de los objetos de tipo contenido
for objContent in listContents:
    lista = re.findall(regexTexts,objContent.content,re.DOTALL)
    for text in lista:
        #obj2.printedTexts.append(parse_text(text[1]))
        parse_text(objContent,text[1])
    


#-- MENU --
def exit_menu():
    print("Saliendo del programa...")
    exit()

def option_1():
     print_struct_tree(listObjects[4])

def option_2():    
     while True:
        pagina = input("Por favor, escribe la página que quieres imprimir (o '0' para volver al menú principal): ")
        if pagina == '0':
            print("Volviendo al menú principal...")
            return
        try:
            numero = int(pagina)
            if 1 <= numero <= 20:
                print_sheet(listContents[numero-1])
                break
            else:
                 print("Número fuera de rango. Por favor, ingresa un número entre 1 y 20.")
        except ValueError:
            print("Entrada no válida. Por favor, ingresa un número (o '0' para volver al menú principal): ")

def option_3():
     print_pdf(listContents)

def option_4():  
     while True:
        pagina = input("Por favor, escribe la página del texto que quieres imprimir (o '0' para volver al menú principal): ")
        if pagina == '0':
            print("Volviendo al menú principal...")
            return
        try:
            numero = int(pagina)
            if 1 <= numero <= 20:
                show_printed_texts(listContents[numero-1])
                id_text = input("\nSelecciona un id para imprimir: ")
                try:
                    print_text_by_id(id_text, listContents[numero-1])
                    break
                except:
                    print("Entrada no válida, no has insertado un id válido para etsa página")
            else:
                 print("Número fuera de rango. Por favor, ingresa un número entre 1 y 20.")
        except ValueError:
            print("Entrada no válida. Por favor, ingresa un número (o '0' para volver al menú principal): ")

def option_5():
     while True:
        id = input("Por favor, escribe el id del objeto. Debe ser un número del 1 al 2933 (o '0' para volver al menú principal): ")
        if id == '0':
            print("Volviendo al menú principal...")
            return
        try:
            numero = int(id)
            if 1 <= numero <= 2933:
                print_referencias(listObjects[numero-1])
                break
            else:
                 print("Número fuera de rango. Por favor, ingresa un número entre 1 y 2933.")
        except ValueError:
            print("Entrada no válida. Por favor, ingresa un número entre 1 y 2933 (o '0' para volver al menú principal): ")

def option_6():
    while True:
        print()
        print("0. Volver la menú principal")
        print("1. Modificar una referencia de un objeto")
        print("2. Modificar un texto de un objeto")

        opcion = input("Selecciona una opción (0-2): ")

        if opcion == '0':
            print("Volviendo al menú principal...")
            return
        

        elif opcion == '1':
            id_objeto = input("Por favor, escribe el id del objeto. Debe ser un número del 1 al 2933 (o '0' para volver al menú principal): ")
            if id_objeto == '0':
                print("Volviendo al menú principal...")
                return
            try:
                numero = int(id_objeto)
                if 1 <= numero <= 2933:
                    modificar_referencia(listObjects[numero-1])
                    break
                else:
                    print("Número fuera de rango. Por favor, ingresa un número entre 1 y 2933.")
            except ValueError:
                print("Entrada no válida. Por favor, ingresa un número entre 1 y 2933 (o '0' para volver al menú principal): ")


        elif opcion == '2':
                   
            pagina = input("Por favor, escribe la página del texto que quieres imprimir (o '0' para volver al menú principal): ")
            if pagina == '0':
                print("Volviendo al menú principal...")
                return
            try:
                numero = int(pagina)
                if 1 <= numero <= 20:
                    show_printed_texts(listContents[numero-1])
                    id_text = input("\nSelecciona un id para modificar: ")
                    try:
                        print_text_by_id(id_text, listContents[numero-1])

                        modificar_texto(id_text, listContents[numero-1])
                        break
                    except:
                        print("Entrada no válida, no has insertado un id válido para etsa página")
                else:
                    print("Número fuera de rango. Por favor, ingresa un número entre 1 y 20.")
            except ValueError:
                print("Entrada no válida. Por favor, ingresa un número (o '0' para volver al menú principal): ")


        else:
            print("Entrada no válida. Inserte un número del 0 al 2")


def option_7():

    new_content = modificar_pdf()


    new_file_path = "c:/Users/34629/Documents/UNIVERSIDAD/TFG/newFile.txt"
    with open(new_file_path, 'w', encoding='utf-8') as archivo:
        archivo.write(new_content)
    print()
    print("Nuevo archivo creado...")
    print()

def option_8():
    while True:
        id = input("Por favor, escribe el id del objeto. Debe ser un número del 1 al 2933 (o '0' para volver al menú principal): ")
        if id == '0':
            print("Volviendo al menú principal...")
            return
        try:
            numero = int(id)
            if 1 <= numero <= 2933:
                gestionar_hijos(numero)
                break
            else:
                 print("Número fuera de rango. Por favor, ingresa un número entre 1 y 2933.")
        except ValueError:
            print("Entrada no válida. Por favor, ingresa un número entre 1 y 2933 (o '0' para volver al menú principal): ")

# Método que muestra el menú de opciones
def show_menu():
    print("-----------------------------------------------------------------------------------")
    print("\nMenú de opciones")
    print("1. Imprimir el árbol de estructura del PDF")
    print("2. Imprimir una página del PDF")
    print("3. Imprimir el PDF entero")
    print("4. Imprimir un texto por id")
    print("5. Imprimir refrencias de un objeto")
    print("6. Modificar objeto")
    print("7. Descargar PDF")
    print("8. Gestionar los hijos de un objeto")
    print("9. Salir")
    print("-----------------------------------------------------------------------------------")

# Método principal del programa
def main():
    while True:
        show_menu()
        opcion = input("Selecciona una opción (1-9): ")
        
        if opcion == '1':
            option_1()
        elif opcion == '2':
            option_2()
        elif opcion == '3':
            option_3()
        elif opcion == '4':
            option_4()
        elif opcion == '5':
            option_5()
        elif opcion == '6':
            option_6()
        elif opcion == '7':
            option_7()
        elif opcion == '8':
            option_8()
        elif opcion == '9':
            exit_menu()
        else:
            print("Opción no válida. Por favor, intenta de nuevo.")
        print()

# Llamada al método principal del programa
if __name__ == "__main__":
    main()