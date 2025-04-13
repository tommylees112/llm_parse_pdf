"""
Extract obituary data from text with the following fields:

Required fields:
- name: Full name of the deceased
- obituary_text: The complete obituary text
- dates: Birth and death years

Derived fields:
- age: Calculated as (death_year - birth_year)
- word_count: Number of words in the obituary text

Note: The format varies throughout the document, so robust regex patterns are needed
to correctly separate each obituary and extract the key information.

Example:
{
    "obituary_id": "5",
    "name": "Robert (Bob) Alexander Creswell",
    "obituary_text": "...",
    "word_count": 1363,
    "age": 62  # Calculated from dates (2010-1948)
}
"""

import json
import re
from pathlib import Path

from loguru import logger

# import datetime


def extract_obituary_data(text):
    """
    Extracts name, obituary text, dates, age, and word count from obituary text.

    Args:
        text (str): A string containing one or more obituaries.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              extracted data for one obituary.
    """

    obituaries = []

    # Find all obituary entries using a more robust pattern
    obituary_pattern = (
        r"\*\*([A-Za-z\s\(\)]+)\s+(\d{4})\s*-\s*(\d{4})\*\*[\n\r]+((?:(?!\*\*).)*)"
    )
    matches = re.finditer(obituary_pattern, text, re.DOTALL)

    for match in matches:
        obituary_data = {"obituary_id": str(len(obituaries) + 1)}

        # Extract name
        obituary_data["name"] = match.group(1).strip()

        # Extract dates
        try:
            birth_year = int(match.group(2))
            death_year = int(match.group(3))
        except (ValueError, TypeError):
            birth_year = None
            death_year = None

        obituary_data["birth_year"] = birth_year
        obituary_data["death_year"] = death_year

        # Extract obituary text
        obituary_text = match.group(4).strip()
        obituary_data["obituary_text"] = obituary_text

        # Calculate age and word count if birth and death years are available
        if birth_year is not None and death_year is not None:
            obituary_data["age"] = death_year - birth_year
            obituary_data["word_count"] = len(obituary_text.split())
        else:
            obituary_data["age"] = None
            obituary_data["word_count"] = 0

        obituaries.append(obituary_data)

    return obituaries


if __name__ == "__main__":
    # apply the function to the provided text data/AlpineJournalObituary/AlpineJournalObituary.md
    markdown_dir = Path("./data/AlpineJournalObituary")
    assert markdown_dir.exists(), f"Directory {markdown_dir} does not exist"
    markdown_file = markdown_dir / "AlpineJournalObituary.md"
    assert markdown_file.exists(), f"File {markdown_file} does not exist"

    # read the text from the
    with open(markdown_file, "r") as f:
        markdown_text = f.read()
    main_text_parts = re.findall(r"<main>(.*?)</main>", markdown_text, re.DOTALL)
    text = "\n".join(main_text_parts)
    # text = """
    #     **Page 405**

    #     **Chris Astill 1956 - 2009**

    #     'Chris Astill was the one on Liathach.'

    #     Avalanches in Scotland on 30 December 2009 claimed the lives of three climbers; [cite: 639, 640] the news that Chris was one of them slowly entered my brain, cutting like a chainsaw through my feelings. [cite: 640, 641] Since Jimmy Jewel had died so many years ago now, I'd promised myself I would not allow myself ever to get hurt again. [cite: 641, 642] Some hope!

    #     Chris and his partner Jo had been in the Highlands, over on his favourite north-west coast, as usual over the Christmas period. [cite: 642, 643] He had called me to say 'hello' and to ask where he could get snowshoes. [cite: 643, 644] He was obviously aware of the great depth of new snow that had come down and it was still falling. [cite: 644, 645] I pointed to Martin Moran for the snowshoe advice and asked Chris and Jo to call in again, like last year, on their way back to Derbyshire. [cite: 645, 646] It wouldn't happen. Nearing the top of a gully on Liathach, the avalanche took him down some considerable way. [cite: 646, 647] His pal Oliver climbed down and got to him. Although Chris was talking, things were serious and the helicopter rescue was probably minutes, hours, too late, who knows, as he died later that night in Inverness hospital. [cite: 647, 648] I was, and still am, devastated.

    #     'Eyeeup kid, ow's it goin' youth?' The standard Nottingham welcome was always truly meant with real friendship. [cite: 648, 649] Chris was that kind of guy, one of the nicest blokes I've known for nearly 40 years. [cite: 649, 650] Intellectually always very smart, a neat and determined man and without question a great all-round climber. [cite: 650, 651] To me he had no faults, except maybe even for me, being a touch too keen, ready for any escapade: a Scottish winter adventure, that wet rock climb, our South American odyssey to Aconcagua with my clients, Bill, David and Sandra, an Alpine adventure in Chamonix or even a Himalayan sojourn. [cite: 651, 652] He was the true all-rounder; one of my best climbing friends. [cite: 652, 653] I first met him when I was a 19 or 20-year-old. [cite: 653, 654, 655] When we were both coming through the ranks, grabbing those elite north faces, I would bump into him everywhere: in the UK, mostly in Llanberis but often in Stoney cafe; [cite: 654, 655] in the Alps, on the Bioley, then Snell's Field; and later, Pierre D'Ortaz, legendary campsites used by the best alpinists of the times, as mere breaks between great climbs. [cite: 656, 657] Lately he would join fellow AC members and venture up bigger peaks in the Himalaya. [cite: 656, 657] (He had joined the club in 1985.)

    #     We soon became good friends. [cite: 657, 658, 659, 660] Sadly, as I grew older and slowed down, with my last 14 years being spent up north, and with that golden era of British alpinism long gone, it would be a less regular meeting, with those famous words ringing out across the Llanberis high street, or in Pete's Eats, or as I would unload the sacks at Ynys for the weekend. [cite: 658, 659, 660] I was grateful for the climbing clubs we were both in – the AC, Climbers Club and the Fell & Rock. [cite: 659, 660] These kept us more in contact over recent years and I hoped would do so for a few more to come. [cite: 660, 661] I was looking forward to some more great times together. Mid December 2009 brought one more such event. [cite: 661, 662, 663, 664] I'd intended to fly down to Manchester to avoid the eight-hour drive. [cite: 662, 663, 664] Chris assured me he would be waiting at the arrivals for me, and was intent on whisking me to Tideswell and the local pub, to join the boys and of course, Jo, his beautiful lady, would as always be by his side. [cite: 664, 665, 666, 667] The plan was thwarted by heavy snow in the Highlands. [cite: 664, 665, 666, 667] I tried twice more to fly but on both occasions the runway was out of action. [cite: 666, 667] Eventually I had to drive, or I would miss my final CC committee meeting as president. [cite: 667, 668, 669, 670, 671] It was dark by the time my sat nav got me to within shouting distance of Chris and Jo's lovely house in their neat little village. [cite: 668, 669, 670, 671] Chris stood proudly outside his house, and directed me to a parking spot alongside his brand new garage. [cite: 669, 670, 671] He had restricted his free time for quite a while to build it, and a super building it had turned out to be. [cite: 670, 671] 'I've only got the loft insulation to put in and that's that,' he announced proudly. [cite: 671, 672, 673] So sad to know he wouldn't see the finishing line. [cite: 672, 673] I spent a great weekend with Chris, Jo, and Rachel, one of his two daughters from his first marriage. [cite: 673, 674, 675, 676, 677] On the Sunday, Chris and I had a special day together on Kinder Scout. [cite: 674, 675, 676, 677] It would be my first visit to this wild place, and not only would we ascend to the bleak plateau, we'd walk through the mire to the Downfall, which I really wanted see, and Chris announced we'd do a rock climb on one of the high crags there. [cite: 675, 676, 677] Ok, it would only be a Severe, but in that damp and gloomy atmosphere, you could argue about my keenness. [cite: 676, 677] Chris, however, was on fire, and I would not dowse him. [cite: 677, 678, 679, 680] We had a great day, the Downfall was in full flow and I pondered the sight when frozen. [cite: 678, 679, 680] Later, on the rock route, I was watching carefully for sandbags. [cite: 679, 680] On a convenient ledge I craftily avoided finishing the top pitch with an, 'I'll bring you up.' [cite: 680, 681, 682] It's not clear where it goes from here?' Chris came up, took the rack and proceeded to show me why I held him in such esteem, as he smoothly climbed the slimy, green groove, which I had been convinced wasn't the normal way forward. [cite: 681, 682] Recently we'd been doing some talking. Our future alpine plans, given some breaks in my annual summer guiding programme, and Chris's ability to break off his 'pole counting' for BT, were for the Frêney, even the Innominata and the Pueterey Integral. [cite: 682, 683, 684] How I could put back the clock now. His new day job, recently acquired after a successful and rewarding career in the mining industry, always amused us all, but it secured the finances along with Jo's outdoor centre instructor role, and he was happy strolling along the fells in many different locations in the country, and in all weathers. [cite: 683, 684] I'm sure there was much more to it than counting poles, but I never got the chance to find out more. [cite: 684] He told me he felt so alive.

    #     Smiler Cuthbertson

    #     **Page 407**

    #     **Patrick 'Paddy' Boulter 1927 - 2009**

    #     Professor 'Paddy' Boulter, who died in November 2009, aged 82, played a key role in establishing the first breast cancer screening centre in Britain. [cite: 685, 686, 687] Away from the operating theatre or lecture hall, Paddy was never happier than when he was heading up a hill – be it in Nepal, the Alps or simply Penrith Beacon near his Cumbrian home. [cite: 686, 687] Paddy was born in Annan, Dumfriesshire, in 1927 and always took pride in his Scottish ancestry. [cite: 687, 688, 689, 690] The family moved to Wimbledon then back north to Carlisle where Paddy attended Carlisle Grammar School and developed his love of hill-walking and climbing in the Lake District. [cite: 688, 689, 690] On one occasion he cajoled friends to cycle from Carlisle to Coniston, where they climbed the 'Old Man', then pedalled home. [cite: 690, 691, 692, 693, 694] After training at Guy's and a spell at the Middlesex, Paddy returned to Guy's as Senior Registrar, before going on to become a consultant surgeon at the Royal Surrey County Hospital, Guildford. [cite: 691, 692, 693, 694] It was here, together with a consultant radiologist, that he made his name by developing the use of mammography to detect early cancers; [cite: 691, 692, 693, 694] he set up a pioneering unit in Surrey in 1978 with his wife Mary (they had married in 1946) running a team of 100 volunteers who guided people in outlying clinics in the area. [cite: 693, 694] Meanwhile in Edinburgh, Professor Patrick Forrest was working along similar lines. [cite: 693, 694] After 10 years their joint study showed that early diagnosis had reduced breast cancer death rates by 25%, an achievement that persuaded the government to adopt such screening nationally. [cite: 695, 696, 697] When Paddy retired from Guildford he and Mary moved back to Cumbria. However Paddy's medical career continued; [cite: 695, 696, 697] he became president of the Royal College of Surgeons of Edinburgh from 1991 to 1994 and was made an honorary fellow of the Royal Australian College of Surgeons. [cite: 697, 698, 699] He travelled the world lecturing and teaching and was greatly respected by his students, although their enthusiasm dimmed occasionally when they were dragged up mountains in his wake. [cite: 698, 699] He never travelled without his boots.Paddy joined the Association of British Members of the Swiss Alpine Club (ABMSAC) in 1968 and advanced rapidly, becoming a committee member in 1971, vice-president in 1973 and president in 1978. A man of great charm and humour, he was also recognised as a shrewd chairman of meetings and wise counsellor. [cite: 699, 700, 701, 702, 703] He became a member of the Alpine Club in 1972.

    #     A past ABMSAC Journal shows that 1971, perhaps a typical year, included two weeks in the Lakes, skiing at Obergurgl, climbing in Chamonix, St Luc and Zermatt, a family holiday in Corsica, and finally an ascent of the Puig de Teix above Valdemosa in Majorca – all this on top of his medical duties. [cite: 700, 701, 702, 703] Later he and Mary developed a special affection for Bivio near the Julier Pass in Switzerland. [cite: 701, 702, 703] Other shared passions were fly-fishing – their Cumbrian cottage is close by the River Eden – and alpine plants. [cite: 702, 703] Among Paddy's other claims to fame were to have played cricket on the Plain de la Morte, a 22-hour day in Colorado, 200 miles of walking and 56 tops in Galloway and a visit to the Khyber Pass. [cite: 703, 704, 705] He climbed with John Hunt in Nepal and he and Mary went ski mountaineering with Harry Archer in the Engadine on many occasions. [cite: 704, 705] The meticulousness observed in his medical research was evident also in a record he kept of every hill and mountain climbed from 1961; [cite: 705, 706, 707] in 30 years he ascended nearly 4000 named tops.

    #     Paddy is survived by Mary, his two daughters Jenny and Anne, five grandchildren and five great-grandchildren. [cite: 706, 707, 708] Wendell Jones

    #     **Roger Childs 1933 - 2010**

    #     Roger Childs, who died in Spain on 8 June 2010 after some years of debilitating illness, was a dynamic man of many parts who combined athleticism with artistic sensibility. [cite: 707, 708, 709, 710, 711] Coming relatively late to serious mountaineering, he then embraced it with the same enthusiasm as had characterised his already action-packed life. [cite: 708, 709, 710, 711] Educated at Cranbrook School, Kent, Roger qualified as a chartered accountant and, after gaining his professional experience with an accountancy firm in Rochester, joined UNRWA in Beirut in 1959 when the scars of the 1956 Suez debacle were still manifest. [cite: 709, 710, 711] His experiences in this troubled part of the world left him with an abiding interest in Middle Eastern affairs. [cite: 710, 711, 712, 713] Apart from skiing at the Cedars of Lebanon, waterskiing in the Mediterranean, and crewing in Beirut Yacht Club races, it was here that he met his wife Belita. [cite: 711, 712, 713] They worked together as part of an amalgam of nationalities that comprised UNRWA (UN Relief and Works Agency for Palestine Refugees) and in 1961 were married in Tehran. [cite: 712, 713] That same year they moved to Jerusalem where Roger was appointed head of UNRWA operations for Jordan, with particular responsibility for running refugee camps. [cite: 713, 714, 715] After returning to London in 1963, the couple bought an elegant house
    #     </main>
    #     <image>
    #     Paddy Boulter, Kuala Lumpur, 1993.
    #     </image>
    #     <image>
    #     Roger Childs
    #     </image>

    #     **Page 409**
    #     <main>
    #     in Greenwich, and in 1965 Roger joined Rank Xerox where he worked for the next 14 years, at first London based, but with overall responsibility for the firm's Scandinavian operations, and later as second in command of the Paris office. [cite: 714, 715] As befitted a proper Englishman, he habitually walked to work through the streets of Paris with a furled umbrella. [cite: 715, 716, 717, 718] After Xerox, Roger's independent bent took him into management with several British industrial companies. [cite: 716, 717, 718] In 1983 he and his cousin bought MEDC, a tiny electrical design and manufacturing company in Pinxton, Nottinghamshire. [cite: 717, 718] This turning point in his career coincided with his first serious essay into ski mountaineering, a High Level Route traverse as a member of a Downhill Only club party. [cite: 718, 719, 720, 721, 722] Roger's drive, enthusiasm and management skills were eventually to turn MEDC into a highly successful business venture with an annual turnover of £13m. [cite: 719, 720, 721, 722] For many years, Roger played a pivotal role in the artistic life of Greenwich and Blackheath. [cite: 720, 721, 722] He helped revive, and for many years served as Chairman of, the Blackheath Conservatoire which was originally founded to train and encourage young musicians, dancers and artists. [cite: 721, 722] He himself had taken up drawing and painting in the 1980s and this remained a solace to the end. [cite: 722, 723, 724, 725] Apart from a life-long love of sailing, especially in the Aegean which he explored with family and friends as part-owner of a 41ft ketch, he was active in many sports including fell running with the annual Trevelyan Hunt in the Lakes, squash, and tennis (with which he persevered even after serious illness). [cite: 723, 724, 725] But most particularly, in the years before working in the Middle East, his passion was rugby. [cite: 724, 725, 726, 727, 728, 729] He represented his county, Kent, and played regularly for Blackheath, oldest of Rugby Union clubs. [cite: 725, 726, 727, 728, 729] In the Club's centenary match against Newport, he scored the winning try. [cite: 726, 727, 728, 729] After his 1983 High Level Route, Roger turned his mind to exploratory ski mountaineering and, in the following year, joined my party with the object of completing a ski traverse of the Cairngorms. [cite: 727, 728, 729] Aborted when I dislocated my shoulder, Roger's companionship provided balm when we were holed up for nine hours in the Avon bothy, while David and Anna Williams undertook a hazardous night-time ski to raise a helicopter rescue. [cite: 728, 729, 730, 731, 732, 733] Thereafter, Roger became a regular member of the team, completing the three testing final sections of the Pyrenean High Route, the ascent of half a dozen peaks, and a final settling of scores with Aneto and Posets. [cite: 729, 730, 731, 732, 733] We went on to make a skein of Scottish ski ascents together, mixed with the occasional alpine foray, but it was in Spain that Roger's mountaineering penchant found truest expression. [cite: 730, 731, 732, 733] One of his many projects had been to rehabilitate Prado Lobero (Wolf Meadow) a wildly beautiful finca that he and Belita had bought near Candeleda beneath Spain's Sierra de Gredos. [cite: 731, 732, 733] Here, they set about converting derelict farmhouses into dwellings of delight, excavating fresh springs, and transforming unkempt fields into fruitful orchards. [cite: 732, 733, 734, 735] Prada Lobero became the launch-pad for many pioneer ski mountaineering expeditions and ascents in Spain's less frequented ranges such as the Gredos, Picos de Europa, Montes Carrionas, and the Cordillera Cantabrica. [cite: 733, 734, 735] Roger's enthusiasm, savoir faire, and his intimate knowledge of the country, its language and people, its paradors and hostels, wines and gastronomy made these unforgettable experiences. [cite: 734, 735] In April 1994 he was a valued member of Derek Fordham's Svalbard expedition which, after long, cold days of pulk slogging, climbed the archipelago's highest peak, Newtontoppen. [cite: 735, 736, 737] In 1996, he made a solo ascent of Cotopaxi (5600m), and in 1999 joined a pioneer ski tour to lesser-known parts of Greece including Falakro. [cite: 736, 737] We returned the following year to the Pindus and climbed the country's second summit Smolikas (2637m). [cite: 737, 738, 739] By now the ill-health that was to blight the last decade of Roger's life had already taken hold, and to have completed that exhausting day in his condition, demanded the exceptional qualities that characterised the man. [cite: 738, 739] Fittingly, his last ski mountaineering expedition was to the Lebanon in 2001 but, game to the end, he subsequently attended two ASC meets in Andermatt and Briançon. [cite: 739, 740, 741] Roger became a member of the Alpine Ski Club in 1987, and for several years served as the Eagle Ski Club's honorary treasurer. [cite: 740, 741] Already an FRGS, he was elected to the Geographical Club in 1997, and in that same year, with over a dozen unguided ski mountaineering tours, several of them pioneer, and well over 30 ascents to his credit, he was elected an aspirant member of the Alpine Club.Although Roger's last few years were a struggle against illness, he never lost his zest for living, love of nature, humour, or skills as a raconteur. [cite: 741, 742, 743] Ever lovingly supported and sustained throughout those difficult times by his wife Belita, his daughters Sophie, Alexa, Julia and Anya, he confronted every setback with an abiding Christian faith, and with the same courage and determination that had made him such a stalwart mountain companero. [cite: 742, 743] Roger Childs was a most hospitable, devoted, life-enhancing family man of many gifts. [cite: 743, 744, 745, 746, 747] He will be greatly missed by all who shared the numerous fields of activity that he had graced but most of all by his wife, daughters and grandchildren.John Harding

    #     **Robert (Bob) Alexander Creswell 1948 - 2010**

    #     The public often assume a head for heights is the first requirement of a mountaineer. [cite: 744, 745, 746, 747] But, as Bob Creswell proved, curiosity and enthusiasm will take you a lot further. [cite: 745, 746, 747] As a child, his family liked to remind him, he was so frightened of heights that he insisted on being carried down stairs. [cite: 746, 747, 748, 749] Yet as an adult, and despite a later than usual start in the hills and a demanding career, he climbed mountains on every continent, often in the company of Jagged Globe guides, who counted him a good friend as well as a capable client. [cite: 747, 748, 749] From early forays in the Welsh and Scottish hills, he went on to explore the Altai in central Asia, climb hills in Antarctica, make an attempt on Denali in Alaska, and have a string of successes in South America,
    #     """

    obituary_list = extract_obituary_data(text)
    logger.info(f"Found {len(obituary_list)} obituaries")

    # save the obituary_list to a json file
    with open("obituary_list.json", "w") as f:
        json.dump(obituary_list, f)

    # for obituary in obituary_list:
    #     print(obituary)
