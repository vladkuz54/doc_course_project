import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

import bcrypt

from backend.dal import Session
from backend.dal.db_models import (
    DBModels,
    DriverRequests,
    Drivers,
    FuelRecords,
    InsurancePolicies,
    Notifications,
    RepairRecords,
    Routes,
    RouteStops,
    Users,
    Vehicles,
)

TODAY = date.today()
NOW = datetime.now().replace(second=0, microsecond=0)


def days(n):
    return TODAY + timedelta(days=n)


def at(n, hour=8):
    return datetime.combine(days(n), datetime.min.time()).replace(hour=hour)


def user(username, role, password="password"):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return Users(username=username, password_hash=hashed, role=role)


def build():
    admin = user("admin", "ADMIN", "admin")

    petrenko = Drivers(
        user=user("petrenko", "DRIVER"),
        full_name="Петренко Іван Олександрович",
        license_categories=["B", "C"],
        experience_years=12,
        license_expiry_date=days(900),
        medical_check_date=days(-100),
        medical_valid_until=days(265),
    )
    kovalenko = Drivers(
        user=user("kovalenko", "DRIVER"),
        full_name="Коваленко Олег Петрович",
        license_categories=["B"],
        experience_years=4,
        license_expiry_date=days(20),
        medical_check_date=days(-200),
        medical_valid_until=days(165),
    )
    shevchenko = Drivers(
        user=user("shevchenko", "DRIVER"),
        full_name="Шевченко Андрій Миколайович",
        license_categories=["B", "C", "CE"],
        experience_years=20,
        license_expiry_date=days(1500),
        medical_check_date=days(-370),
        medical_valid_until=days(-5),
        medical_check_status="EXPIRED",
    )
    bondar = Drivers(
        user=user("bondar", "DRIVER"),
        full_name="Бондар Сергій Васильович",
        license_categories=["B", "C"],
        experience_years=8,
        license_expiry_date=days(400),
        medical_check_date=days(-30),
        medical_valid_until=days(335),
    )
    melnyk = Drivers(
        user=user("melnyk", "DRIVER"),
        full_name="Мельник Віктор Іванович",
        license_categories=["B"],
        experience_years=15,
        license_expiry_date=days(600),
        medical_check_date=days(-300),
        medical_valid_until=days(65),
        employment_status="DISMISSED",
    )

    man = Vehicles(
        make="MAN TGS",
        year=2019,
        vin="WMA06XZZ9KP123456",
        required_license_category="C",
        technical_state="Справний",
    )
    renault = Vehicles(
        make="Renault Master",
        year=2021,
        vin="VF1MA000965432101",
        required_license_category="B",
        technical_state="Справний",
    )
    volvo = Vehicles(
        make="Volvo FH16",
        year=2017,
        vin="YV2RT40A9HB765432",
        required_license_category="CE",
        technical_state="Потребує ТО",
    )
    sprinter = Vehicles(
        make="Mercedes Sprinter",
        year=2020,
        vin="WDB9066331S246810",
        required_license_category="B",
        technical_state="Справний",
    )
    gazel = Vehicles(
        make="ГАЗ 3302",
        year=2008,
        vin="X9633020082468013",
        required_license_category="B",
        technical_state="Списаний",
        status="DECOMMISSIONED",
    )

    def stops(*addresses):
        return [RouteStops(order_no=i, address=a) for i, a in enumerate(addresses, 1)]

    routes = [
        Routes(
            driver=petrenko,
            vehicle=man,
            distance=240.0,
            departure_at=at(-10),
            started_at=at(-10),
            completed_at=at(-10, 17),
            status="COMPLETED",
            stops=stops(
                "Львів, вул. Городоцька 359",
                "Тернопіль, вул. Микулинецька 46",
                "Хмельницький, вул. Шевченка 70",
            ),
        ),
        Routes(
            driver=kovalenko,
            vehicle=renault,
            distance=100.0,
            departure_at=at(-3),
            started_at=at(-3),
            completed_at=at(-3, 12),
            status="COMPLETED",
            stops=stops(
                "Львів, вул. Городоцька 359",
                "Стрий, вул. Шевченка 85",
                "Трускавець, вул. Бориславська 20",
            ),
        ),
        Routes(
            driver=petrenko,
            vehicle=man,
            distance=135.0,
            departure_at=at(0, 7),
            started_at=at(0, 7),
            status="IN_PROGRESS",
            stops=stops(
                "Львів, вул. Городоцька 359", "Івано-Франківськ, вул. Галицька 201"
            ),
        ),
        Routes(
            driver=bondar,
            vehicle=sprinter,
            distance=30.0,
            departure_at=at(2),
            status="PLANNED",
            stops=stops("Львів, вул. Городоцька 359", "Жовква, вул. Львівська 12"),
        ),
        Routes(
            driver=kovalenko,
            vehicle=None,
            distance=220.0,
            departure_at=at(5),
            status="PLANNED",
            stops=stops(
                "Львів, вул. Городоцька 359",
                "Луцьк, вул. Рівненська 76",
                "Рівне, вул. Київська 40",
            ),
        ),
        Routes(
            driver=None,
            vehicle=None,
            distance=265.0,
            departure_at=at(7),
            status="PLANNED",
            stops=stops(
                "Львів, вул. Городоцька 359",
                "Мукачево, вул. Пряшівська 10",
                "Ужгород, вул. Собранецька 150",
            ),
        ),
        Routes(
            driver=melnyk,
            vehicle=renault,
            distance=80.0,
            departure_at=at(-20),
            status="CANCELLED",
            stops=stops("Львів, вул. Городоцька 359", "Мостиська, вул. Грушевського 5"),
        ),
    ]

    fuel = [
        FuelRecords(
            vehicle=man, date=days(-10), liters=180.0, amount=Decimal("9540.00")
        ),
        FuelRecords(
            vehicle=man, date=days(-1), liters=150.0, amount=Decimal("7950.00")
        ),
        FuelRecords(
            vehicle=renault, date=days(-3), liters=55.0, amount=Decimal("2915.00")
        ),
        FuelRecords(
            vehicle=sprinter, date=days(-6), liters=60.0, amount=Decimal("3180.00")
        ),
        FuelRecords(
            vehicle=volvo, date=days(-25), liters=300.0, amount=Decimal("15900.00")
        ),
    ]

    repairs = [
        RepairRecords(
            vehicle=man,
            date=days(-60),
            type="SERVICE_TO",
            status="DONE",
            description="ТО-2, заміна масла та фільтрів",
            amount=Decimal("8200.00"),
        ),
        RepairRecords(
            vehicle=renault,
            date=days(-40),
            type="REPAIR",
            status="DONE",
            description="Заміна гальмівних колодок",
            amount=Decimal("3400.00"),
        ),
        RepairRecords(
            vehicle=volvo,
            date=days(3),
            type="SERVICE_TO",
            status="PLANNED",
            description="Планове ТО-1",
        ),
        RepairRecords(
            vehicle=sprinter,
            date=days(14),
            type="INSPECTION",
            status="PLANNED",
            description="Щорічний техогляд",
        ),
    ]

    insurance = [
        InsurancePolicies(
            vehicle=man,
            date=days(-200),
            amount=Decimal("12500.00"),
            start_date=days(-200),
            end_date=days(165),
        ),
        InsurancePolicies(
            vehicle=renault,
            date=days(-355),
            amount=Decimal("6800.00"),
            start_date=days(-355),
            end_date=days(10),
        ),
        InsurancePolicies(
            vehicle=volvo,
            date=days(-100),
            amount=Decimal("18900.00"),
            start_date=days(-100),
            end_date=days(265),
        ),
        InsurancePolicies(
            vehicle=sprinter,
            date=days(-30),
            amount=Decimal("7200.00"),
            start_date=days(-30),
            end_date=days(335),
        ),
    ]

    license_request = DriverRequests(
        driver=kovalenko,
        type="LICENSE_UPDATE",
        new_license_category="C",
        new_license_expiry_date=days(3650),
        created_at=NOW - timedelta(days=1),
    )
    medical_request = DriverRequests(
        driver=shevchenko,
        type="MEDICAL_CHECK",
        created_at=NOW - timedelta(hours=5),
    )
    approved_request = DriverRequests(
        driver=bondar,
        type="MEDICAL_CHECK",
        status="APPROVED",
        created_at=NOW - timedelta(days=30),
    )

    def make_notifications():
        return [
            Notifications(
                type="LICENSE_UPDATE_REQUEST",
                related_entity="driver_requests",
                related_id=license_request.id,
                created_at=license_request.created_at,
                text="Коваленко О. П. просить оновити посвідчення до категорії C",
            ),
            Notifications(
                type="MEDICAL_CHECK_REQUEST",
                related_entity="driver_requests",
                related_id=medical_request.id,
                created_at=medical_request.created_at,
                text="Шевченко А. М. подав запит на підтвердження медогляду",
            ),
            Notifications(
                type="MAINTENANCE_SCHEDULED",
                related_entity="vehicles",
                related_id=volvo.id,
                created_at=NOW - timedelta(days=2),
                text=f"Заплановано ТО для Volvo FH16 на {repairs[2].date:%d.%m.%Y}",
            ),
            Notifications(
                type="INSURANCE_EXPIRING",
                related_entity="vehicles",
                related_id=renault.id,
                created_at=NOW,
                text=f"Страховка Renault Master спливає {days(10):%d.%m.%Y}",
            ),
            Notifications(
                type="LICENSE_EXPIRING",
                related_entity="drivers",
                related_id=kovalenko.id,
                created_at=NOW,
                text=f"Посвідчення Коваленка О. П. спливає {days(20):%d.%m.%Y}",
            ),
            Notifications(
                recipient_id=kovalenko.user_id,
                type="LICENSE_EXPIRING",
                related_entity="drivers",
                related_id=kovalenko.id,
                created_at=NOW,
                text=f"Посвідчення Коваленка О. П. спливає {days(20):%d.%m.%Y}",
            ),
            Notifications(
                type="MEDICAL_CHECK_DUE",
                related_entity="drivers",
                related_id=shevchenko.id,
                created_at=NOW - timedelta(days=5),
                text="Медогляд Шевченка А. М. прострочено",
                is_read=True,
            ),
            Notifications(
                recipient_id=shevchenko.user_id,
                type="MEDICAL_CHECK_DUE",
                related_entity="drivers",
                related_id=shevchenko.id,
                created_at=NOW - timedelta(days=5),
                text="Медогляд Шевченка А. М. прострочено",
            ),
        ]

    objs = [
        admin,
        petrenko,
        kovalenko,
        shevchenko,
        bondar,
        melnyk,
        man,
        renault,
        volvo,
        sprinter,
        gazel,
        *routes,
        *fuel,
        *repairs,
        *insurance,
        license_request,
        medical_request,
        approved_request,
    ]
    return objs, make_notifications


async def seed():
    db = DBModels()
    await db.drop_db()
    await db.init_db()
    async with Session() as session:
        objs, make_notifications = build()
        session.add_all(objs)
        await session.flush()
        session.add_all(make_notifications())
        await session.commit()
    print(
        "Database seeded. Logins: admin/admin, petrenko|kovalenko|shevchenko|bondar|melnyk / password"
    )


if __name__ == "__main__":
    asyncio.run(seed())
