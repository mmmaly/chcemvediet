# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.workdays.workdays import HolidaySet, FixedHoliday, EasterHoliday


# Holidays in SR since 1994.
# Source: 241/1993 Z.z., 201/1996 Z.z., 442/2001 Z.z.
HOLIDAYS = HolidaySet(
        FixedHoliday(day=1,  month=1,  first_year=1994, last_year=None),  # Deň vzniku Slovenskej republiky
        FixedHoliday(day=6,  month=1,  first_year=1994, last_year=None),  # Zjavenie Pána (Traja králi a vianočný sviatok pravoslávnych kresťanov)
        EasterHoliday(days=-2,         first_year=1994, last_year=None),  # Veľkonočný piatok
        EasterHoliday(days=+1,         first_year=1994, last_year=None),  # Veľkonočný pondelok
        FixedHoliday(day=1,  month=5,  first_year=1994, last_year=None),  # Sviatok práce
        FixedHoliday(day=8,  month=5,  first_year=1997, last_year=None),  # Deň víťazstva nad fašizmom
        FixedHoliday(day=5,  month=7,  first_year=1994, last_year=None),  # Sviatok svätého Cyrila a Metoda
        FixedHoliday(day=29, month=8,  first_year=1994, last_year=None),  # Výročie Slovenského národného povstania
        FixedHoliday(day=1,  month=9,  first_year=1994, last_year=None),  # Deň Ústavy Slovenskej republiky
        FixedHoliday(day=15, month=9,  first_year=1994, last_year=None),  # Sviatok Panny Márie Sedembolestnej, patrónky Slovenska
        FixedHoliday(day=1,  month=11, first_year=1994, last_year=None),  # Sviatok všetkých svätých
        FixedHoliday(day=17, month=11, first_year=2001, last_year=None),  # Deň boja za slobodu a demokraciu
        FixedHoliday(day=24, month=12, first_year=1994, last_year=None),  # Štedrý deň
        FixedHoliday(day=25, month=12, first_year=1994, last_year=None),  # Prvý sviatok vianočný
        FixedHoliday(day=26, month=12, first_year=1994, last_year=None),  # Druhý sviatok vianočný
        )

