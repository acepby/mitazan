from telegram import (KeyboardButton,ReplyKeyboardMarkup,ReplyKeyboardRemove)
from telegram.ext import (Updater,CommandHandler,MessageHandler, Filters,RegexHandler,ConversationHandler,Job)
from dotenv import load_dotenv,find_dotenv
from os import getenv
import logging
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from pytz import timezone
import pytz
from datetime import date,datetime,time,timedelta
from  praytimes import PrayTimes

tf = TimezoneFinder()
prayTimes = PrayTimes()
prayTimes.setMethod('Karachi')
#geolocator
geolocator = Nominatim(user_agent="mitazan")
load_dotenv(find_dotenv())
telegram_token = getenv('TELEGRAM_TOKEN')



#enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
logger = logging.getLogger(__name__)

LOCATION,JADWAL,LOKASIMU = range(3)
location_keyboard = KeyboardButton(text="Lokasi by GPS",  request_location=True)

def getOffset(target):
    utc = pytz.utc
    today = datetime.now()
    tz_target = timezone(tf.certain_timezone_at(lat=target['lat'],lng=target['lng']))
    today_target=tz_target.localize(today)
    today_utc= utc.localize(today)
    return (today_utc - today_target).total_seconds()/3600

def getLokasi(loc):
    #geolocator=Nominatim(user_agent='mitazan')
    location = geolocator.reverse(loc)
    return location.address

def getAlamat(text):
    location = geolocator.geocode(text)
    return (location.latitude,location.longitude)

def getImsakiyah(bot,update,date):
    return 'imsakiyah hari ini {}'.format(date)

def start(bot,update):
    reply_keyboard = [[location_keyboard],["Alamat"]]
    update.message.reply_text(
      'Hi! kenalin ni MIT bot.\n'
      'Saat ini bot hanya support jadwal imsakiyah. \n'
      'Untuk Penggunaan cukup pilih tombol aja \n'
      'Lokasi by GPS akan mencari alamat berdasar GPS.\n'
      'Alamat adalah untuk input manual alamat anda \n'
      'Perintah yang ada saat ini adalah : \n '
      '/start untuk memulai aplikasi \n'
      '/cancel untuk selesai \n'
      'untuk perintah setting dan notifikasi belum ada',
      reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return LOCATION

def location(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    chat_id = update.message.chat_id
    mylokasi=(user_location.latitude,user_location.longitude)
    latlong = dict({'lat':user_location.latitude,'lng':user_location.longitude})
    lokasi = getLokasi(mylokasi)
    offset = getOffset(latlong)
    today = date.today()
    #getImsakiyah menampilkan imsakiyah hari ini
    #tgl='15 mei'
    #jadwal = getImsakiyah(bot,update,tgl)
    #setAlarmImsakiyah 
    '''alarm imsakiyah akan atur imsakiyah hari ini dengan waktu yang terdekat'''
    jadwal = getImsakiyah(mylokasi,offset)
    #jadwal = ', '.join("{!s}={!r}".format(key,val) for (key,val) in jadwal.items())
    jadwal = formatJadwal(jadwal)

    logger.info("Location of %s: %f / %f", user.first_name, user_location.latitude,
                user_location.longitude)
    update.message.reply_text("Hi {} lokasi anda adalah  {}\n "
                               "Imsakiyah {}\n"
                               "{}".format(user.first_name,lokasi,today,jadwal))

    return ConversationHandler.END

def setlokasi(bot,update):
    update.message.reply_text('Ketikan alamatmu, '
                              'misal : jakarta')
    return LOKASIMU

def getLokasimu(bot,update):
    alamat = update.message.text
    mylokasi= getAlamat(alamat) #(user_location.latitude,user_location.longitude)
    latlong = dict({'lat':mylokasi[0],'lng':mylokasi[1]})
    lokasi = getLokasi(mylokasi)
    offset = getOffset(latlong)
    jadwal = getImsakiyah(mylokasi,offset)
    #jadwal = ', '.join("{!s}={!r}".format(key,val) for (key,val) in jadwal.items())
    jadwal = formatJadwal(jadwal)
    update.message.reply_text("Imsakiyah di alamatmu \n"
                              "{}".format(jadwal))
    return ConversationHandler.END

def formatJadwal(jadwal):
    formated = '\n'.join("{} : {}".format(key,val) for key,val in sorted(jadwal.items(), key=lambda p:p[1]))
    return formated


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

'''def lokasi(lat,long):
    geolocator=Nominatim(user_agent='mitazan')
    location = geolocator.reverse(lat,long)
    return location.address '''
#loc =(-7.7500127,110.3606701)

#def ImsakiyahReminder(bot,job):


def getImsakiyah(loc,off_set):
    tgl =datetime.now()
    waktu = tgl.replace(second=0,microsecond=0)
    waktu = waktu.time()
    print(date.today())
    times = prayTimes.getTimes(date.today(), loc, off_set)
    imsakiyah=['Imsak','Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'] 
    jadwal = dict()
    for i in imsakiyah: #['Imsak','Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
        jadwal.update({i:times[i.lower()]})
    return jadwal

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(telegram_token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            LOCATION: [MessageHandler(Filters.location, location),RegexHandler('^(Alamat)$',setlokasi),CommandHandler('alamat',setlokasi),],
            LOKASIMU: [MessageHandler(Filters.text,getLokasimu),]

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
