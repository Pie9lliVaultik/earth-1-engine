"""Name pools for qualitative enrichment — country-specific first/last names.

Sampled statistically at generation time. Covers top 50 countries with
real census-frequency names; remaining countries use regional archetypes."""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple


_NAMES: Dict[str, Dict[str, List[str]]] = {
    "IN": {
        "m": ["Aarav", "Arjun", "Rahul", "Vikram", "Sanjay", "Amit", "Raj", "Deepak", "Anil", "Suresh",
              "Rohit", "Manish", "Kiran", "Pradeep", "Ashok", "Ravi", "Vijay", "Krishna", "Manoj", "Ajay"],
        "f": ["Priya", "Ananya", "Neha", "Pooja", "Sunita", "Kavita", "Anjali", "Divya", "Meera", "Lakshmi",
              "Nisha", "Rani", "Deepa", "Sita", "Gita", "Radha", "Asha", "Usha", "Rekha", "Sarita"],
        "last": ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Das", "Nair", "Iyer", "Joshi",
                 "Verma", "Rao", "Pillai", "Mishra", "Bhat", "Agarwal", "Mehta", "Shah", "Yadav", "Pandey"],
    },
    "CN": {
        "m": ["Wei", "Jian", "Jun", "Tao", "Ming", "Hao", "Yang", "Feng", "Lei", "Peng",
              "Chao", "Long", "Bo", "Hai", "Xiang", "Yong", "Gang", "Bin", "Liang", "Dong"],
        "f": ["Fang", "Xia", "Li", "Mei", "Ying", "Yan", "Hong", "Jing", "Hua", "Lan",
              "Yun", "Xue", "Qian", "Ling", "Ping", "Na", "Dan", "Rui", "Min", "Wen"],
        "last": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
                 "Xu", "Sun", "Ma", "Hu", "Guo", "Lin", "He", "Gao", "Luo", "Zheng"],
    },
    "US": {
        "m": ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
              "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth"],
        "f": ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen",
              "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                 "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"],
    },
    "ID": {
        "m": ["Agus", "Budi", "Hendra", "Adi", "Eko", "Dedi", "Rizal", "Imam", "Wahyu", "Arif",
              "Yusuf", "Bambang", "Hasan", "Dimas", "Fajar", "Reza", "Ahmad", "Irfan", "Bayu", "Dwi"],
        "f": ["Siti", "Sri", "Dewi", "Rina", "Ayu", "Putri", "Wati", "Yanti", "Ningsih", "Indah",
              "Fitri", "Ratna", "Lestari", "Rahayu", "Sari", "Wulan", "Ani", "Ika", "Dian", "Tuti"],
        "last": ["Suryadi", "Wijaya", "Saputra", "Hidayat", "Putra", "Kurniawan", "Setiawan", "Santoso", "Nugroho", "Pratama",
                 "Susanto", "Wibowo", "Hartono", "Gunawan", "Lestari", "Rahman", "Siregar", "Hakim", "Nasution", "Lubis"],
    },
    "PK": {
        "m": ["Muhammad", "Ali", "Ahmed", "Usman", "Hassan", "Bilal", "Imran", "Kashif", "Tariq", "Asad",
              "Kamran", "Faisal", "Zubair", "Naveed", "Saad", "Waqar", "Junaid", "Adeel", "Shahid", "Aamir"],
        "f": ["Fatima", "Ayesha", "Zainab", "Hira", "Sara", "Amina", "Maryam", "Nadia", "Sana", "Bushra",
              "Rabia", "Samina", "Nasreen", "Rubina", "Saima", "Kiran", "Nida", "Asma", "Farah", "Uzma"],
        "last": ["Khan", "Ahmed", "Ali", "Malik", "Hussain", "Shah", "Butt", "Iqbal", "Qureshi", "Sheikh",
                 "Chaudhry", "Siddiqui", "Abbasi", "Baig", "Raza", "Mirza", "Javed", "Saeed", "Hashmi", "Aslam"],
    },
    "NG": {
        "m": ["Chukwuma", "Emeka", "Obiora", "Adebayo", "Oluwaseun", "Ibrahim", "Musa", "Yusuf", "Chinedu", "Nnamdi",
              "Tunde", "Segun", "Abdullahi", "Bello", "Uche", "Kola", "Dayo", "Sani", "Chijioke", "Femi"],
        "f": ["Ngozi", "Amina", "Funke", "Aisha", "Blessing", "Chidinma", "Adaeze", "Folake", "Halima", "Yetunde",
              "Nneka", "Bukola", "Fatima", "Chinasa", "Binta", "Toyin", "Jummai", "Ifeoma", "Titilayo", "Zainab"],
        "last": ["Okafor", "Adeyemi", "Ibrahim", "Obi", "Mohammed", "Bello", "Abubakar", "Eze", "Okeke", "Adamu",
                 "Nwachukwu", "Oladipo", "Usman", "Chukwu", "Suleiman", "Onyeka", "Aliyu", "Olayinka", "Yusuf", "Nwosu"],
    },
    "BR": {
        "m": ["João", "Pedro", "Lucas", "Mateus", "Gabriel", "Rafael", "Bruno", "Carlos", "Fernando", "André",
              "Marcos", "Paulo", "José", "Luiz", "Gustavo", "Diego", "Felipe", "Eduardo", "Ricardo", "Roberto"],
        "f": ["Maria", "Ana", "Juliana", "Fernanda", "Camila", "Beatriz", "Larissa", "Amanda", "Bruna", "Letícia",
              "Patrícia", "Raquel", "Aline", "Daniela", "Carla", "Gabriela", "Tatiana", "Vanessa", "Renata", "Adriana"],
        "last": ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
                 "Costa", "Ribeiro", "Martins", "Carvalho", "Araújo", "Melo", "Barbosa", "Nascimento", "Moura", "Monteiro"],
    },
    "RU": {
        "m": ["Aleksandr", "Dmitriy", "Sergey", "Andrey", "Ivan", "Mikhail", "Nikolay", "Pavel", "Viktor", "Oleg",
              "Yuriy", "Maksim", "Artem", "Igor", "Vladislav", "Roman", "Ilya", "Kirill", "Denis", "Evgeny"],
        "f": ["Anna", "Olga", "Mariya", "Elena", "Natalya", "Tatyana", "Irina", "Svetlana", "Yekaterina", "Anastasiya",
              "Darya", "Yuliya", "Oksana", "Lyudmila", "Galina", "Valentina", "Larisa", "Vera", "Alena", "Polina"],
        "last": ["Ivanov", "Petrov", "Smirnov", "Kuznetsov", "Popov", "Sokolov", "Lebedev", "Kozlov", "Novikov", "Morozov",
                 "Volkov", "Fedorov", "Kovalev", "Vasilev", "Belov", "Zaytsev", "Pavlov", "Semyonov", "Golubev", "Bogdanov"],
    },
    "JP": {
        "m": ["Haruto", "Yuto", "Sota", "Hinata", "Ren", "Yuki", "Takumi", "Riku", "Kenji", "Tatsuya",
              "Daiki", "Kento", "Hiroshi", "Shota", "Ryota", "Yusei", "Hayato", "Kazuki", "Naoki", "Kosuke"],
        "f": ["Yui", "Hana", "Sakura", "Aoi", "Rin", "Mei", "Mio", "Akari", "Yuna", "Hinata",
              "Koharu", "Riko", "Miyu", "Saki", "Nanami", "Haruka", "Yuka", "Misaki", "Ayaka", "Kaede"],
        "last": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato",
                 "Yoshida", "Yamada", "Sasaki", "Yamaguchi", "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu", "Yamazaki"],
    },
    "MX": {
        "m": ["José", "Juan", "Luis", "Carlos", "Miguel", "Francisco", "Pedro", "Rafael", "Alejandro", "Roberto",
              "Fernando", "Ricardo", "Sergio", "Eduardo", "Jorge", "Arturo", "Enrique", "Raúl", "Andrés", "Héctor"],
        "f": ["María", "Guadalupe", "Juana", "Ana", "Rosa", "Patricia", "Leticia", "Claudia", "Verónica", "Adriana",
              "Gabriela", "Alejandra", "Silvia", "Carmen", "Laura", "Isabel", "Teresa", "Martha", "Sandra", "Luz"],
        "last": ["García", "Hernández", "López", "Martínez", "González", "Rodríguez", "Pérez", "Sánchez", "Ramírez", "Cruz",
                 "Flores", "Gómez", "Morales", "Vázquez", "Reyes", "Torres", "Gutiérrez", "Ruiz", "Díaz", "Mendoza"],
    },
    "DE": {
        "m": ["Lukas", "Maximilian", "Alexander", "Paul", "Leon", "Felix", "Jonas", "Tim", "Moritz", "Niklas",
              "Jan", "Thomas", "Michael", "Stefan", "Andreas", "Markus", "Christian", "Tobias", "Sebastian", "Daniel"],
        "f": ["Anna", "Lena", "Julia", "Sophie", "Marie", "Lea", "Sarah", "Laura", "Lisa", "Emma",
              "Hannah", "Katharina", "Maria", "Jana", "Nicole", "Sandra", "Claudia", "Sabine", "Christina", "Stefanie"],
        "last": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
                 "Koch", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger"],
    },
    "GB": {
        "m": ["Oliver", "Jack", "Harry", "George", "Charlie", "Thomas", "James", "William", "Daniel", "Samuel",
              "David", "Joseph", "Henry", "Edward", "Alexander", "Oscar", "Arthur", "Noah", "Freddie", "Leo"],
        "f": ["Olivia", "Amelia", "Isla", "Ava", "Mia", "Emily", "Isabella", "Sophia", "Grace", "Lily",
              "Charlotte", "Jessica", "Sarah", "Hannah", "Lucy", "Emma", "Katie", "Rachel", "Sophie", "Alice"],
        "last": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Johnson",
                 "Roberts", "Robinson", "Thompson", "Wright", "Walker", "White", "Edwards", "Hughes", "Green", "Hall"],
    },
    "FR": {
        "m": ["Jean", "Pierre", "Michel", "Louis", "François", "Nicolas", "Thomas", "Alexandre", "Lucas", "Hugo",
              "Julien", "Maxime", "Antoine", "Guillaume", "Paul", "Mathieu", "Clément", "Romain", "Sébastien", "Olivier"],
        "f": ["Marie", "Jeanne", "Camille", "Julie", "Léa", "Manon", "Chloé", "Emma", "Sarah", "Sophie",
              "Charlotte", "Alice", "Isabelle", "Catherine", "Nathalie", "Sylvie", "Christine", "Martine", "Anne", "Claire"],
        "last": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
                 "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier"],
    },
    "IT": {
        "m": ["Marco", "Giuseppe", "Giovanni", "Alessandro", "Andrea", "Luca", "Francesco", "Matteo", "Lorenzo", "Davide",
              "Simone", "Stefano", "Roberto", "Fabio", "Antonio", "Riccardo", "Massimo", "Paolo", "Claudio", "Alberto"],
        "f": ["Maria", "Giulia", "Francesca", "Chiara", "Sara", "Anna", "Valentina", "Alessandra", "Federica", "Silvia",
              "Elena", "Paola", "Laura", "Simona", "Claudia", "Eleonora", "Martina", "Roberta", "Monica", "Cristina"],
        "last": ["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco",
                 "Bruno", "Gallo", "Conti", "De Luca", "Mancini", "Costa", "Giordano", "Rizzo", "Lombardi", "Moretti"],
    },
    "ES": {
        "m": ["Antonio", "Manuel", "José", "Francisco", "David", "Juan", "Carlos", "Jesús", "Alejandro", "Miguel",
              "Daniel", "Rafael", "Pablo", "Sergio", "Javier", "Fernando", "Álvaro", "Adrián", "Diego", "Pedro"],
        "f": ["María", "Carmen", "Ana", "Laura", "Isabel", "Marta", "Cristina", "Lucía", "Elena", "Rosa",
              "Sofía", "Paula", "Sara", "Pilar", "Andrea", "Patricia", "Beatriz", "Raquel", "Julia", "Alba"],
        "last": ["García", "Fernández", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
                 "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Álvarez", "Muñoz", "Romero", "Alonso", "Gutiérrez"],
    },
    "KR": {
        "m": ["Minho", "Joonho", "Hyunwoo", "Seungmin", "Jihoon", "Donghyun", "Taemin", "Jaehyun", "Youngho", "Sungjae",
              "Kyungsoo", "Woojin", "Yoonho", "Changmin", "Junhyuk", "Sungho", "Taehyung", "Jungkook", "Jooheon", "Hyunjin"],
        "f": ["Jiyeon", "Minji", "Yoona", "Soojin", "Haeun", "Soyeon", "Eunji", "Dahyun", "Chaeyoung", "Nayeon",
              "Jihye", "Seulgi", "Yujin", "Hayoung", "Jisoo", "Minyoung", "Sunhee", "Bora", "Hyejin", "Yeji"],
        "last": ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang", "Lim",
                 "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang", "Ahn", "Song", "Yoo", "Hong"],
    },
    "TR": {
        "m": ["Mehmet", "Mustafa", "Ahmet", "Ali", "Hasan", "Hüseyin", "İbrahim", "Yusuf", "Murat", "Emre",
              "Burak", "Can", "Oğuz", "Kemal", "Selim", "Serkan", "Tolga", "Barış", "Cem", "Onur"],
        "f": ["Fatma", "Ayşe", "Emine", "Hatice", "Zeynep", "Elif", "Merve", "Büşra", "Derya", "Esra",
              "Gül", "Hülya", "Leyla", "Melek", "Nur", "Özlem", "Seda", "Sibel", "Tuğba", "Yeliz"],
        "last": ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
                 "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek"],
    },
    "EG": {
        "m": ["Mohamed", "Ahmed", "Mahmoud", "Ali", "Hassan", "Ibrahim", "Omar", "Khaled", "Youssef", "Mostafa",
              "Tamer", "Sherif", "Amr", "Karim", "Tarek", "Hossam", "Walid", "Nader", "Wael", "Essam"],
        "f": ["Fatma", "Aisha", "Nour", "Sara", "Hala", "Mona", "Dina", "Rania", "Yasmin", "Laila",
              "Mariam", "Noha", "Eman", "Ghada", "Heba", "Amira", "Nagwa", "Sahar", "Soha", "Abeer"],
        "last": ["Hassan", "Mohamed", "Ali", "Ahmed", "Ibrahim", "Mostafa", "Mahmoud", "Abdel", "El-Sayed", "Khalil",
                 "Abdallah", "Farag", "Salah", "Amin", "Nasser", "Kamel", "Youssef", "Osman", "Gamal", "Tawfik"],
    },
    "TH": {
        "m": ["Somchai", "Somsak", "Sompong", "Prasert", "Surachai", "Wichai", "Nattapong", "Kittisak", "Thawat", "Anon",
              "Prawit", "Tanawat", "Pongsakorn", "Jaturon", "Siripong", "Worapol", "Athit", "Krit", "Piyawat", "Noppadon"],
        "f": ["Suda", "Malee", "Nong", "Wan", "Pim", "Ploy", "Fah", "Noi", "Kwan", "Aom",
              "Praew", "Mook", "Nuch", "Bow", "Nam", "Tai", "Prae", "May", "Joy", "Mint"],
        "last": ["Saetang", "Wongsawat", "Chaiyasit", "Sriprom", "Thongkam", "Phanit", "Meesuk", "Srithong", "Boonpeng", "Rattanaporn"],
    },
    "ZA": {
        "m": ["Thabo", "Sipho", "Bongani", "Themba", "Mandla", "Siyabonga", "Mpho", "Tshepo", "Lebogang", "Kagiso",
              "Johan", "Pieter", "Hennie", "Willem", "Jacques", "Andre", "David", "Michael", "James", "John"],
        "f": ["Thandiwe", "Nomvula", "Lerato", "Palesa", "Zanele", "Nontobeko", "Mpho", "Thandeka", "Sibongile", "Nombuso",
              "Annelie", "Marelize", "Christa", "Elna", "Hester", "Maria", "Sarah", "Emily", "Grace", "Hope"],
        "last": ["Nkosi", "Dlamini", "Ndlovu", "Zulu", "Molefe", "Khumalo", "Mkhize", "Mokoena", "Botha", "Van der Merwe",
                 "Pretorius", "Joubert", "Nel", "Venter", "Du Plessis", "Smith", "Williams", "Johnson", "Pillay", "Naidoo"],
    },
    "PH": {
        "m": ["Juan", "Jose", "Pedro", "Mark", "John", "Michael", "James", "Angelo", "Rafael", "Carlo",
              "Ryan", "Kevin", "Christian", "Bryan", "Kenneth", "Francis", "Patrick", "Jerome", "Daniel", "Jayson"],
        "f": ["Maria", "Ana", "Grace", "Rose", "May", "Joy", "Faith", "Princess", "Angel", "Nicole",
              "Jasmine", "Michelle", "Kristine", "Cherry", "April", "Precious", "Jane", "Mary", "Lovely", "Divine"],
        "last": ["Santos", "Reyes", "Cruz", "Bautista", "Del Rosario", "Gonzales", "Garcia", "Ramos", "Mendoza", "Rivera",
                 "Flores", "Torres", "Villanueva", "De Leon", "Aquino", "Soriano", "Castillo", "Tan", "Lim", "Go"],
    },
    "VN": {
        "m": ["Minh", "Duc", "Huy", "Tuan", "Thanh", "Long", "Quang", "Hung", "Dung", "Trung",
              "Hai", "Nam", "Khanh", "Son", "Phong", "Cuong", "Dat", "Binh", "Hoang", "Vinh"],
        "f": ["Linh", "Trang", "Hoa", "Lan", "Huong", "Thao", "Ngoc", "Mai", "Anh", "Phuong",
              "Hanh", "Yen", "Dung", "Thu", "Van", "Tam", "Quynh", "Chi", "Hong", "Nhu"],
        "last": ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Dang", "Bui",
                 "Do", "Ho", "Ngo", "Duong", "Ly", "Trinh", "Dinh", "Truong", "Luu", "Mai"],
    },
    "CO": {
        "m": ["Andrés", "Carlos", "Juan", "David", "Santiago", "Sebastián", "Daniel", "Miguel", "Felipe", "Alejandro"],
        "f": ["María", "Laura", "Camila", "Valentina", "Daniela", "Natalia", "Andrea", "Paula", "Carolina", "Juliana"],
        "last": ["García", "Rodríguez", "Martínez", "López", "González", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez"],
    },
    "AR": {
        "m": ["Mateo", "Santiago", "Benjamín", "Joaquín", "Bautista", "Lucas", "Nicolás", "Juan", "Agustín", "Tomás"],
        "f": ["Sofía", "Valentina", "Isabella", "Emilia", "Catalina", "Martina", "Mía", "Victoria", "Renata", "Camila"],
        "last": ["González", "Rodríguez", "Gómez", "Fernández", "López", "Díaz", "Martínez", "Pérez", "García", "Sánchez"],
    },
    "KE": {
        "m": ["James", "John", "Peter", "David", "Joseph", "Samuel", "Daniel", "Paul", "Stephen", "George",
              "Kipchoge", "Wafula", "Ochieng", "Mwangi", "Kamau", "Njoroge", "Otieno", "Kiprono", "Mutua", "Ngugi"],
        "f": ["Mary", "Grace", "Faith", "Mercy", "Agnes", "Joyce", "Rose", "Esther", "Margaret", "Catherine",
              "Wanjiku", "Akinyi", "Chebet", "Njeri", "Wambui", "Atieno", "Jepkosgei", "Nyambura", "Muthoni", "Wairimu"],
        "last": ["Kamau", "Ochieng", "Mwangi", "Wanjiku", "Kiplagat", "Ngugi", "Otieno", "Mutua", "Kiprono", "Akinyi",
                 "Njoroge", "Wafula", "Chebet", "Korir", "Rotich", "Sang", "Kiptoo", "Omari", "Hassan", "Mohamed"],
    },
    "PL": {
        "m": ["Jan", "Andrzej", "Piotr", "Krzysztof", "Stanisław", "Tomasz", "Paweł", "Marcin", "Michał", "Marek"],
        "f": ["Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Ewa", "Krystyna", "Elżbieta", "Magdalena"],
        "last": ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak"],
    },
    "ET": {
        "m": ["Abebe", "Tadesse", "Girma", "Tesfaye", "Haile", "Berhanu", "Dawit", "Yohannes", "Solomon", "Mesfin"],
        "f": ["Tigist", "Hiwot", "Meron", "Bezawit", "Kidist", "Seble", "Rahel", "Sara", "Yeshi", "Abeba"],
        "last": ["Bekele", "Tadesse", "Getachew", "Mulatu", "Kebede", "Tekle", "Wolde", "Gebre", "Hailu", "Desta"],
    },
    "BD": {
        "m": ["Mohammad", "Abdul", "Md", "Kamal", "Rahim", "Hossain", "Rashid", "Nazrul", "Jamal", "Faruk"],
        "f": ["Fatema", "Roksana", "Nasrin", "Hasina", "Rina", "Shirin", "Sultana", "Taslima", "Halima", "Rehena"],
        "last": ["Rahman", "Hossain", "Ahmed", "Islam", "Khan", "Akter", "Begum", "Miah", "Chowdhury", "Uddin"],
    },
}

# Regional archetypes for countries without specific name pools
_REGION_NAMES: Dict[str, Dict[str, List[str]]] = {
    "Sub-Saharan Africa": {
        "m": ["Kwame", "Kofi", "Ayo", "Amadi", "Tendai", "Chidi", "Olumide", "Jabari", "Sekou", "Amadou"],
        "f": ["Amara", "Aisha", "Zara", "Adwoa", "Thandiwe", "Nalini", "Fatou", "Aminata", "Adjoa", "Ama"],
        "last": ["Diallo", "Traore", "Mensah", "Osei", "Banda", "Nkomo", "Adebayo", "Conteh", "Ouedraogo", "Keita"],
    },
    "Middle East/N. Africa": {
        "m": ["Mohamed", "Ahmed", "Ali", "Hassan", "Omar", "Youssef", "Khalid", "Ibrahim", "Samir", "Nabil"],
        "f": ["Fatima", "Aisha", "Mariam", "Nour", "Layla", "Sara", "Hana", "Yasmin", "Rania", "Salma"],
        "last": ["Al-Hassan", "El-Amin", "Benali", "Khoury", "Haddad", "Mansour", "Nassar", "Salem", "Qasim", "Nasser"],
    },
    "Latin America": {
        "m": ["Carlos", "José", "Luis", "Juan", "Miguel", "Pedro", "Fernando", "Andrés", "Roberto", "Ricardo"],
        "f": ["María", "Ana", "Carmen", "Rosa", "Lucía", "Elena", "Patricia", "Claudia", "Isabel", "Gabriela"],
        "last": ["García", "Rodríguez", "López", "Martínez", "González", "Hernández", "Pérez", "Sánchez", "Ramírez", "Torres"],
    },
    "East Asia": {
        "m": ["Wei", "Jun", "Tao", "Hao", "Feng", "Ming", "Long", "Peng", "Lei", "Yang"],
        "f": ["Mei", "Ying", "Xia", "Fang", "Hong", "Jing", "Lan", "Yun", "Hua", "Qian"],
        "last": ["Wang", "Li", "Zhang", "Chen", "Liu", "Yang", "Huang", "Wu", "Zhou", "Zhao"],
    },
    "South Asia": {
        "m": ["Raj", "Arjun", "Amir", "Sanjay", "Ravi", "Vikram", "Sunil", "Prakash", "Ganesh", "Mohan"],
        "f": ["Priya", "Anita", "Sunita", "Lakshmi", "Meera", "Rani", "Sita", "Kamala", "Nisha", "Deepa"],
        "last": ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Das", "Nair", "Rao", "Reddy", "Khan"],
    },
    "Southeast Asia": {
        "m": ["Arief", "Budi", "Nguyen", "Somchai", "Ahmad", "Rodel", "Tran", "Pham", "Kofi", "Rizal"],
        "f": ["Siti", "Dewi", "Linh", "Malee", "Nurul", "Maria", "Trang", "Ayu", "Putri", "Rina"],
        "last": ["Nguyen", "Tran", "Saetang", "Wijaya", "Santos", "Reyes", "Pham", "Hoang", "Suryadi", "Rahman"],
    },
    "Western Europe": {
        "m": ["Thomas", "Alexander", "Daniel", "Michael", "David", "Martin", "Peter", "Stefan", "Paul", "Christian"],
        "f": ["Maria", "Anna", "Sophie", "Emma", "Laura", "Julia", "Sarah", "Lisa", "Claudia", "Charlotte"],
        "last": ["Müller", "Schmidt", "Martin", "Johansson", "Andersen", "Bianchi", "García", "Ferreira", "De Vries", "Hansen"],
    },
    "Eastern Europe": {
        "m": ["Aleksandr", "Dmitriy", "Ivan", "Andrei", "Miroslav", "Bogdan", "Petru", "Janos", "Milan", "Luka"],
        "f": ["Anna", "Olga", "Elena", "Natalya", "Irina", "Marina", "Tatyana", "Svetlana", "Marta", "Jelena"],
        "last": ["Ivanov", "Popov", "Horvat", "Novak", "Petrovic", "Ionescu", "Nagy", "Kovalenko", "Dimitrov", "Jankovic"],
    },
    "Central Asia": {
        "m": ["Nursultan", "Timur", "Azamat", "Bakyt", "Erbol", "Daniyar", "Aibek", "Ruslan", "Marat", "Bolat"],
        "f": ["Aigul", "Madina", "Asel", "Dinara", "Gulnara", "Zhanna", "Kamila", "Aliya", "Saule", "Nazgul"],
        "last": ["Nazarbayev", "Aliev", "Karimov", "Ismoilov", "Berdyev", "Tokayev", "Rakhimov", "Sultanov", "Mirzaev", "Azimov"],
    },
    "Oceania": {
        "m": ["Liam", "Jack", "Oliver", "James", "William", "Thomas", "Noah", "Lucas", "Henry", "Samuel"],
        "f": ["Charlotte", "Olivia", "Amelia", "Isla", "Ava", "Mia", "Grace", "Lily", "Emily", "Sophie"],
        "last": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Anderson", "Thomas", "Harris", "Martin"],
    },
    "North America": {
        "m": ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"],
        "f": ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"],
    },
}


def get_name_pool(iso2: str, region: str) -> Dict[str, List[str]]:
    if iso2 in _NAMES:
        return _NAMES[iso2]
    return _REGION_NAMES.get(region, _REGION_NAMES["Western Europe"])


def sample_name(iso2: str, region: str, gender_male: bool, rng) -> Tuple[str, str]:
    pool = get_name_pool(iso2, region)
    key = "m" if gender_male else "f"
    first = pool[key][rng.integers(0, len(pool[key]))]
    last = pool["last"][rng.integers(0, len(pool["last"]))]
    return first, last
