"""
 Direitos Autorais (C) 2020 Dabble Lab - Todos os Direitos Reservados
 Você pode usar, distribuir e modificar este código sob os
 termos e condições definidos no arquivo 'LICENSE.txt', que
 faz parte deste pacote de código-fonte.
 
 Para informações adicionais sobre direitos autorais, por favor
 visite: http://dabblelab.com/copyright
"""

from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.dispatch_components import (AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from twilio.rest import Client

import logging
import json
import random
import requests
import os
import boto3

# Estabelece conexão com a API do Twilio
account_sid = '<substitua pelo seu SID da conta Twilio>'
auth_token = '<substitua pelo seu token de autenticação Twilio>'
messaging_service_sid = '<substitua pelo seu SID do serviço de mensagens Twilio>'
client = Client(account_sid, auth_token)

# Definindo a região do banco de dados, nome da tabela e adaptador de persistência DynamoDB
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)

# Inicializando o logger e definindo o nível para "INFO"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Manipuladores de Intenções (Intent Handlers)

# Este Manipulador é chamado quando a skill é invocada usando apenas o nome de invocação (Ex. Alexa, abra o template quatro)
class LaunchRequestHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma e atributos persistentes
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        skill_name = language_prompts["SKILL_NAME"]
        
        # Tenta carregar o 'phonebook' dos atributos persistentes ou cria um novo
        try:
            phonebook = persistent_attributes['phonebook']
            speech_output = random.choice(language_prompts['WELCOME_BACK']).format(skill_name)
            reprompt = random.choice(language_prompts['WELCOME_BACK_REPROMPT'])
        
        except:
            persistent_attributes['phonebook'] = []
            handler_input.attributes_manager.save_persistent_attributes()
            speech_output = random.choice(language_prompts['WELCOME']).format(skill_name)
            reprompt = random.choice(language_prompts['WELCOME_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
        )


# Manipulador para a intenção de receber um número de telefone
class PhoneNumberIsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("PhoneNumberIsIntent")(handler_input)

    def handle(self, handler_input):
        # Obtém os prompts de idioma e os atributos da sessão
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        
        try:
            # Tenta obter o número de telefone do slot da intenção
            phone_number = handler_input.request_envelope.request.intent.slots["phone_number"].value
            session_attributes['phone_number'] = phone_number
            
            # Define a resposta e o reprompt
            speech_output = random.choice(language_prompts['PHONE_NUMBER_CONFIRMED'])
            reprompt = random.choice(language_prompts['PHONE_NUMBER_CONFIRMED_REPROMPT'])
        except:
            # Resposta caso não consiga entender o número de telefone
            speech_output = random.choice(language_prompts['PHONE_NUMBER_UNCONFIRMED'])
            reprompt = random.choice(language_prompts['PHONE_NUMBER_UNCONFIRMED_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )


# Manipulador para a intenção de receber o nome de um contato
class TheNameIsIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        return is_intent_name("TheNameIsIntent")(handler_input)

    def handle(self, handler_input):
        # Obtém os prompts de idioma e atributos da sessão e persistentes
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        
        try:
            # Recupera o livro de telefone e o nome do contato
            phonebook = persistent_attributes['phonebook']
            contact_name = handler_input.request_envelope.request.intent.slots["contact_name"].value
            phone_number = session_attributes['phone_number']
            
            # Cria e salva o contato completo
            complete_contact = {'contact_name': contact_name, 'phone_number': phone_number}
            phonebook.append(complete_contact)
            
            persistent_attributes['phonebook'] = phonebook
            handler_input.attributes_manager.save_persistent_attributes()
            
            # Define a resposta e o reprompt
            speech_output = random.choice(language_prompts['CONTACT_SAVED'])
            reprompt = random.choice(language_prompts['CONTACT_SAVED_REPROMPT'])
        except:
            # Resposta caso não consiga salvar o contato
            speech_output = random.choice(language_prompts['CONTACT_NOT_SAVED'])
            reprompt = random.choice(language_prompts['CONTACT_NOT_SAVED_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Manipulador para a intenção de salvar um novo contato
class SaveNewContactIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "SaveNewContactIntent"
        return is_intent_name("SaveNewContactIntent")(handler_input)
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        
        # Define a mensagem e o reprompt para salvar um novo contato
        speech_output = random.choice(language_prompts['SAVE_NEW_CONTACT'])
        reprompt = random.choice(language_prompts['SAVE_NEW_CONTACT_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Manipulador para a intenção de enviar uma mensagem de texto
class SendTextMessageIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "SendTextMessageIntent"
        return is_intent_name("SendTextMessageIntent")(handler_input)
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        
        # Define a mensagem e o reprompt para enviar uma mensagem de texto
        speech_output = random.choice(language_prompts['SEND_TEXT_MESSAGE'])
        reprompt = random.choice(language_prompts['SEND_TEXT_MESSAGE_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Manipulador para a intenção de definir a mensagem a ser enviada
class MyMessageIsIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "MyMessageIsIntent"
        return is_intent_name("MyMessageIsIntent")(handler_input)
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma e os atributos da sessão
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        
        try:
            # Tenta obter a mensagem do slot da intenção
            message = handler_input.request_envelope.request.intent.slots["message_text"].value
            session_attributes['message'] = message
            
            # Define a mensagem e o reprompt para confirmação da mensagem recebida
            speech_output = random.choice(language_prompts['MESSAGE_RECEIVED'])
            reprompt = random.choice(language_prompts['MESSAGE_RECEIVED_REPROMPT'])
        except:
            # Resposta em caso de erro na obtenção da mensagem
            speech_output = random.choice(language_prompts['ERROR_WITH_MESSAGE'])
            reprompt = random.choice(language_prompts['ERROR_WITH_MESSAGE_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )


# Manipulador para a intenção de escolher um contato
class ChooseContactIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "ChooseContactIntent"
        return is_intent_name("ChooseContactIntent")(handler_input)
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma e atributos da sessão e persistentes
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        session_attributes = handler_input.attributes_manager.session_attributes
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        
        try:
            # Recupera o livro de telefone e a mensagem
            phonebook = persistent_attributes['phonebook']
            message = session_attributes['message']
            recipient_name = handler_input.request_envelope.request.intent.slots["recipient_name"].value
            
            # Procura pelo contato e envia a mensagem
            for record in phonebook:
                if record['contact_name'] == recipient_name:
                    print("Antes a Mensagem")
                    # Envia a mensagem através do Twilio
                    message = client.messages.create(  
                        messaging_service_sid = messaging_service_sid, 
                        body = message,      
                        to = '+91' + record['phone_number'] 
                    )
                    speech_output = random.choice(language_prompts['MESSAGE_SENT'])
                    reprompt = random.choice(language_prompts['MESSAGE_SENT_REPROMPT'])
                    break
                else:
                    speech_output = random.choice(language_prompts['CONTACT_NOT_FOUND'])
                    reprompt = random.choice(language_prompts['CONTACT_NOT_FOUND_REPROMPT'])
        except:
            # Resposta em caso de erro ao enviar a mensagem
            speech_output = random.choice(language_prompts['MESSAGE_NOT_SENT'])
            reprompt = random.choice(language_prompts['MESSAGE_NOT_SENT_REPROMPT'])
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Manipulador para as intenções de cancelar ou parar a skill
class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "CancelIntent" ou "StopIntent"
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
    
    def handle(self, handler_input):
        # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["CANCEL_STOP_RESPONSE"])
        
        # Retorna a resposta e encerra a sessão
        return (
            handler_input.response_builder
                .speak(speech_output)
                .set_should_end_session(True)
                .response
            )

# Manipulador para a intenção de ajuda
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
    # Verifica se a intenção atual corresponde a "HelpIntent"
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["HELP"])
        reprompt = random.choice(language_prompts["HELP_REPROMPT"])
        
        # Retorna a resposta e mantém a sessão aberta para mais comandos
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )


# Manipulador para intenções não reconhecidas (fallback)
class FallbackIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # Verifica se a intenção atual corresponde a "FallbackIntent"
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    
    def handle(self, handler_input):
    # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        speech_output = random.choice(language_prompts["FALLBACK"])
        reprompt = random.choice(language_prompts["FALLBACK_REPROMPT"])
    
    # Retorna a resposta e mantém a sessão aberta para tentar novamente
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Manipulador para o encerramento da sessão
class SessionEndedRequesthandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # Verifica se é uma solicitação de encerramento de sessão
        return is_request_type("SessionEndedRequest")(handler_input)
    
    def handle(self, handler_input):
        # Registra a razão do encerramento da sessão
        logger.info("Sessão encerrada com a razão: {}".format(handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response

# Manipuladores de Exceções

# Este manipulador de exceção lida com erros de sintaxe ou de roteamento.
class CatchAllExceptionHandler(AbstractExceptionHandler):
    
    def can_handle(self, handler_input, exception):
        # Pode lidar com qualquer exceção
        return True
    
    def handle(self, handler_input, exception):
        # Registra a exceção
        logger.error(exception, exc_info=True)
        
        # Obtém os prompts de idioma
        language_prompts = handler_input.attributes_manager.request_attributes["_"]
        
        # Define a mensagem de erro e reprompt
        speech_output = language_prompts["ERROR"]
        reprompt = language_prompts["ERROR_REPROMPT"]
        
        # Retorna a resposta
        return (
            handler_input.response_builder
                .speak(speech_output)
                .ask(reprompt)
                .response
            )

# Interceptadores

# Interceptador para registrar cada solicitação enviada da Alexa para o nosso endpoint
class RequestLogger(AbstractRequestInterceptor):

    def process(self, handler_input):
        # Registra a solicitação recebida da Alexa
        logger.debug("Solicitação Alexa: {}".format(
            handler_input.request_envelope.request))

# Interceptador para registrar cada resposta que nosso endpoint envia de volta para a Alexa
class ResponseLogger(AbstractResponseInterceptor):

    def process(self, handler_input, response):
        # Registra a resposta enviada para a Alexa
        logger.debug("Resposta Alexa: {}".format(response))

# Interceptador usado para suportar diferentes idiomas e localidades
class LocalizationInterceptor(AbstractRequestInterceptor):

    def process(self, handler_input):
        # Detecta a localidade do usuário
        locale = handler_input.request_envelope.request.locale
        logger.info("Localidade é {}".format(locale))
        
        # Carrega os prompts de idioma correspondentes
        try:
            with open("languages/"+str(locale)+".json") as language_data:
                language_prompts = json.load(language_data)
        except:
            with open("languages/"+ str(locale[:2]) +".json") as language_data:
                language_prompts = json.load(language_data)
        
        # Define os prompts de idioma como atributos de solicitação
        handler_input.attributes_manager.request_attributes["_"] = language_prompts

# Construtor da Skill
sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)
# Adiciona todos os manipuladores de solicitação, manipuladores de exceções e interceptadores
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PhoneNumberIsIntentHandler())
sb.add_request_handler(TheNameIsIntentHandler())
sb.add_request_handler(SaveNewContactIntentHandler())
sb.add_request_handler(SendTextMessageIntentHandler())
sb.add_request_handler(MyMessageIsIntentHandler())
sb.add_request_handler(ChooseContactIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequesthandler())

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler do Lambda
lambda_handler = sb.lambda_handler()