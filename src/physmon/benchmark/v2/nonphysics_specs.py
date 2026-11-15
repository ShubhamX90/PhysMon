"""The sixteen non-physics control structures and their role specs (see `nonphysics.py` for the rules).

Each structure is an everyday word problem (shopping, recipes, classes, savings, tickets, inventory, sharing, work schedules,
league points, library books, garden rows, a school timetable, buses, print jobs) with 2-4 relations and one answer in a unit
word. Each has one role quantity q with three study values and two held-out values, an R wiring (which input q acts on and how),
and two phrasing pairs written exactly as in M0 v2: pair p0 puts the D quantity on another person, shop, class or group in the
same scene at the same time (`other_object_same_scene`); pair p1 puts it on the same object in another event that leaves no state behind
(`same_object_other_event`: history before the stated situation; a change that is made and then reversed is cancellation, not
disconnection, and is not used). Hand-coded solvers are written separately from the node expressions (the independent
route). No sentence uses physics vocabulary; every numeral of a prompt is an input or the one role value.
"""

from __future__ import annotations

from physmon.benchmark.v2 import nonphysics as npx
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

Pair = r2.PhrasePair
I = npx.NPInput  # noqa: E741
N = npx.NPNode
OTHER_EVENT = "same_object_other_event"
CO_PRESENT = "other_object_same_scene"
EQUAL_GROUPS = "Multiplication of equal groups"
TOTAL = "Addition of amounts that are all counted"
REMAINDER = "Subtraction: what is left is the whole minus the part taken"
SHARE = "Division into equal shares"

STRUCTURES: dict[str, npx.NPStructure] = {}
SPECS: dict[str, npx.NPSpec] = {}


def _add(structure: npx.NPStructure, spec: npx.NPSpec) -> None:
    STRUCTURES[structure.structure_id] = structure
    SPECS[structure.structure_id] = spec


# --- NP01 shopping and prices -------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP01", "Change from a purchase", "shopping and prices",
        "Priya buys {n} notebooks at {p} dollars each and one pen for {pen} dollars. She pays with a {paid} dollar bill. Tom is queuing at the next till.",
        "How many dollars of change does she get back?", "change she gets back", "change", "dollars",
        (I("n", "number of notebooks", 3, "notebooks"), I("p", "price of one notebook", 4, "dollars"),
         I("pen", "price of the pen", 2, "dollars"), I("paid", "the bill she pays with", 50, "dollars")),
        (N("books", "n*p", "cost of the notebooks", "dollars", EQUAL_GROUPS, "The notebooks cost the same, so their cost is "
           "the number bought times the price of one."),
         N("bill", "books + pen", "cost of everything she buys", "dollars", TOTAL, "She pays for the notebooks and the pen "
           "together."),
         N("change", "paid - bill", "change she gets back", "dollars", REMAINDER, "The change is what is left of the bill she "
           "pays with after the cost of her purchase is taken out.")),
        lambda n, p, pen, paid: paid - pen - n * p,
        "The solver subtracts the pen and the notebooks one after the other instead of forming the total bill first.",
        ("All prices are in dollars.", "Each notebook costs the same."),
        "Work out what she buys in total, then take it away from the bill she pays with.",
        "The change is less than the bill she pays with and is not negative.",
        ("dollars of change", "change she gets back", "change"), ("change",)),
    npx.NPSpec(
        "NP01", "a sketchbook", "dollars", (7.0, 16.0, 23.0), (15.0, 22.0),
        rv.RelevantWiring("pen", "add", "A sketchbook in her own basket is paid for in the same purchase, so its price is "
                                        "added to the cost of what she buys besides the notebooks."),
        (Pair("p0", "A sketchbook that costs {value} {unit} is {relation}.", "in Priya's basket",
              "in Tom's basket", CO_PRESENT,
              "Tom's basket is another customer's purchase at another till; Priya pays only for her own notebooks and pen, so "
              "the price of Tom's sketchbook is never part of her bill.",
              ("She pays with a 50 dollar bill", "buys 3 notebooks at 4 dollars each"), "a few dollars"),
         Pair("p1", "A sketchbook that costs {value} {unit} {relation}.", "is also in her basket", "was bought by Priya last month", OTHER_EVENT,
              "Priya bought that sketchbook last month; it is no part of what she buys now, so her purchase is still only the notebooks and the pen.",
              ("She pays with a 50 dollar bill", "buys 3 notebooks at 4 dollars each"), "a few dollars"))))

# --- NP02 recipes and portions (counts) ---------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP02", "Cookies left at a fair", "recipes and portions",
        "At a school fair, Dev bakes {trays} trays of cookies with {per_tray} cookies on each tray. He sells {sold} cookies and "
        "gives {gift} to a neighbour. Sara runs the next stall at the fair.",
        "How many cookies does he have left?", "number of cookies he has left", "left", "cookies",
        (I("trays", "number of trays baked", 5, "trays"), I("per_tray", "cookies on one tray", 12, "cookies"),
         I("sold", "cookies sold", 38, "cookies"), I("gift", "cookies given to the neighbour", 6, "cookies")),
        (N("baked", "trays*per_tray", "cookies baked", "cookies", EQUAL_GROUPS, "Every tray holds the same number of cookies."),
         N("gone", "sold + gift", "cookies that left his hands", "cookies", TOTAL, "The cookies sold and the cookies given away "
           "are different cookies, so they add."),
         N("left", "baked - gone", "cookies he has left", "cookies", REMAINDER, "What he has left is what he baked minus what "
           "went away.")),
        lambda trays, per_tray, sold, gift: per_tray * trays - gift - sold,
        "The solver subtracts the sold and the given cookies from the baked cookies one after the other.",
        ("Every tray holds the same number of cookies.", "Cookies sold or given away are not counted again."),
        "Count the cookies baked, count the cookies that went away, and subtract.",
        "The number left is a whole number and is smaller than the number baked.",
        ("cookies does he have left", "cookies left", "number of cookies he has left"), ("left",)),
    npx.NPSpec(
        "NP02", "extra trays of cookies", "trays", (7.0, 9.0, 11.0), (13.0, 15.0),
        rv.RelevantWiring("trays", "add", "Trays that Dev bakes himself add to the number of trays he has, and every tray holds "
                                          "the same number of cookies."),
        (Pair("p0", "{value} {unit} of cookies were also baked {relation}.", "in Dev's oven at the fair",
              "in Sara's oven at the fair", CO_PRESENT,
              "Cookies baked in Sara's oven are Sara's to sell; they are never among the cookies Dev bakes, sells or gives away.",
              ("Dev bakes 5 trays of cookies with 12 cookies on each tray",), "Some trays"),
         Pair("p1", "{value} {unit} of cookies {relation}.", "were also baked by Dev at the fair", "were baked by Dev for last year's fair", OTHER_EVENT,
              "Cookies Dev baked for last year's fair were sold or eaten long ago; they leave nothing among the cookies he has now, so he still has only the trays stated.",
              ("Dev bakes 5 trays of cookies with 12 cookies on each tray",), "Some trays"))))

# --- NP03 inventory -----------------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP03", "Pencils left at the end of the week", "inventory",
        "A stationery shop starts the week with {stock} pencils. It sells {boxes} boxes of {per_box} pencils on Monday and "
        "{loose} loose pencils on Tuesday. The shop next door sells pencils too.",
        "How many pencils does the shop have left at the end of the week?", "number of pencils left", "left", "pencils",
        (I("stock", "pencils at the start of the week", 150, "pencils"), I("boxes", "boxes sold", 4, "boxes"),
         I("per_box", "pencils in one box", 12, "pencils"), I("loose", "loose pencils sold", 35, "pencils")),
        (N("boxed", "boxes*per_box", "pencils sold in boxes", "pencils", EQUAL_GROUPS, "Every box holds the same number of "
           "pencils."),
         N("sold", "boxed + loose", "pencils sold in all", "pencils", TOTAL, "The boxed and the loose pencils are different "
           "pencils, so they add."),
         N("left", "stock - sold", "pencils left", "pencils", REMAINDER, "What is left is the starting stock minus what was "
           "sold.")),
        lambda stock, boxes, per_box, loose: stock - loose - boxes * per_box,
        "The solver subtracts the loose pencils and the boxed pencils from the stock one after the other.",
        ("Every box holds the same number of pencils.", "Nothing else is sold or delivered during the week."),
        "Count the pencils sold in all, then subtract from the starting stock.",
        "The number left is a whole number and is smaller than the starting stock.",
        ("pencils does the shop have left", "pencils left", "number of pencils left"), ("left",)),
    npx.NPSpec(
        "NP03", "pencils taken out of the stock room", "pencils", (8.0, 22.0, 24.0), (11.0, 26.0),
        rv.RelevantWiring("stock", "subtract", "Pencils taken out of this shop's stock room are no longer in the stock the shop "
                                               "holds, so the stock is reduced by that number."),
        (Pair("p0", "{value} {unit} were taken out of {relation} on Thursday.", "the stock room of this shop",
              "the stock room of the shop next door", CO_PRESENT,
              "Pencils taken from the stock room of the shop next door are that shop's stock; they were never among the pencils of "
              "this shop.", ("starts the week with 150 pencils",), "Some pencils"),
         Pair("p1", "{value} {unit} were taken out of the stock room {relation}.", "on Thursday", "the week before", OTHER_EVENT,
              "Pencils taken out the week before the start of the week were already gone when the shop started the week with its stock, so the stated stock already allows for them.",
              ("starts the week with 150 pencils",), "Some pencils"))))

# --- NP04 savings and interest-free payments ----------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP04", "Money left after buying a game", "savings and payments",
        "Lena saves {weekly} dollars each week for {weeks} weeks and starts with {start} dollars in a jar. She then buys a game "
        "for {game} dollars. Her brother Sam lives with her.",
        "How many dollars does she have left?", "money she has left", "left", "dollars",
        (I("weekly", "dollars saved each week", 8, "dollars"), I("weeks", "number of weeks", 6, "weeks"),
         I("start", "dollars in the jar at the start", 35, "dollars"), I("game", "price of the game", 60, "dollars")),
        (N("saved", "weekly*weeks", "dollars saved over the weeks", "dollars", EQUAL_GROUPS, "She saves the same amount every "
           "week."),
         N("jar", "start + saved", "dollars in the jar before the purchase", "dollars", TOTAL, "The starting money and the "
           "savings are different money, so they add."),
         N("left", "jar - game", "dollars left after the purchase", "dollars", REMAINDER, "What she has left is what was in the "
           "jar minus the price of the game.")),
        lambda weekly, weeks, start, game: start + weeks * weekly - game,
        "The solver adds the starting money to the savings and subtracts the price in one expression.",
        ("All amounts are in dollars.", "She saves the same amount every week."),
        "Find what is in the jar after the saving, then take the price of the game away.",
        "She can afford the game, so the money left is not negative.",
        ("dollars does she have left", "money she has left", "left"), ("left",)),
    npx.NPSpec(
        "NP04", "money from an aunt", "dollars", (19.0, 21.0, 28.0), (9.0, 11.0),
        rv.RelevantWiring("start", "add", "Money Lena is given before the purchase goes into her jar with the money she started "
                                          "with."),
        (Pair("p0", "Before the purchase, Lena's aunt gave {relation} {value} {unit}.", "her", "her brother", CO_PRESENT,
              "Money her aunt gave to Lena's brother is her brother's; it never goes into Lena's jar and is not part of what she "
              "has when she buys the game.", ("She then buys a game for 60 dollars",), "some money"),
         Pair("p1", "Lena's aunt gave her {value} {unit} {relation}.", "before the purchase", "for a concert ticket last year", OTHER_EVENT,
              "The money from last year was spent on a concert ticket, so none of it is in the jar now.",
              ("She then buys a game for 60 dollars",), "some money"))))

# --- NP05 tickets and seats ---------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP05", "Free seats for a show", "tickets and seats",
        "A theatre has {rows} rows with {seats} seats in each row. For the evening show, {sold} tickets have been sold and "
        "{staff} seats are kept for staff. A cinema next door shows films too.",
        "How many seats are still free for the evening show?", "number of seats still free", "free", "seats",
        (I("rows", "number of rows", 14, "rows"), I("seats", "seats in one row", 18, "seats"),
         I("sold", "tickets sold", 185, "tickets"), I("staff", "seats kept for staff", 12, "seats")),
        (N("total", "rows*seats", "seats in the theatre", "seats", EQUAL_GROUPS, "Every row has the same number of seats."),
         N("taken", "sold + staff", "seats taken or kept", "seats", TOTAL, "Each ticket is for one seat, and the seats kept for "
           "staff are different seats, so the two numbers add."),
         N("free", "total - taken", "seats still free", "seats", REMAINDER, "The free seats are all the seats minus the taken "
           "ones.")),
        lambda rows, seats, sold, staff: seats * rows - staff - sold,
        "The solver subtracts the staff seats and the sold tickets from the seats of the theatre one after the other.",
        ("Each ticket is for one seat.", "Every row has the same number of seats."),
        "Count all the seats, count the seats that are taken or kept, and subtract.",
        "The number of free seats is not negative and is smaller than the number of seats.",
        ("seats are still free", "still free", "number of seats still free"), ("free",)),
    npx.NPSpec(
        "NP05", "tickets for the evening show", "tickets", (9.0, 13.0, 16.0), (23.0, 27.0),
        rv.RelevantWiring("sold", "add", "Tickets sold for this theatre's evening show are more tickets sold, and each ticket takes "
                                         "one of the seats."),
        (Pair("p0", "{value} {unit} were also sold {relation}.", "for the evening show at this theatre",
              "for the evening show at the cinema next door", CO_PRESENT,
              "Tickets sold for the cinema next door are seats in that cinema; they take no seat of this theatre.",
              ("For the evening show, 185 tickets have been sold",), "Some tickets"),
         Pair("p1", "{value} {unit} were also sold {relation}.", "for the evening show", "for last week's matinee", OTHER_EVENT,
              "Tickets sold for last week's matinee were used last week and take no seat of tonight's show.",
              ("For the evening show, 185 tickets have been sold",), "Some tickets"))))

# --- NP06 sharing and division ------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP06", "Stickers shared among children", "sharing and division",
        "A teacher has {packs} packs with {per_pack} stickers in each pack. She keeps {kept} stickers and shares the rest equally "
        "among {kids} children. Another class works next door.",
        "How many stickers does each child get?", "number of stickers each child gets", "share", "stickers",
        (I("packs", "number of packs", 8, "packs"), I("per_pack", "stickers in one pack", 18, "stickers"),
         I("kept", "stickers she keeps", 24, "stickers"), I("kids", "number of children", 15, "children")),
        (N("total", "packs*per_pack", "stickers in all", "stickers", EQUAL_GROUPS, "Every pack has the same number of stickers."),
         N("rest", "total - kept", "stickers to share", "stickers", REMAINDER, "The stickers she keeps are not shared."),
         N("share", "rest/kids", "stickers each child gets", "stickers", SHARE, "The rest is divided into equal shares, one per "
           "child.")),
        lambda packs, per_pack, kept, kids: (packs * per_pack - kept) / kids,
        "The solver forms the shared stickers in one expression instead of naming the intermediate totals.",
        ("Every pack has the same number of stickers.", "The stickers are shared equally."),
        "Find the stickers to share, then divide them equally among the children.",
        "Every child gets a whole number of stickers and the shares add up to the stickers shared.",
        ("stickers does each child get", "each child get", "number of stickers each child gets"), ("share",)),
    npx.NPSpec(
        "NP06", "children who went home", "children", (7.0, 11.0, 12.0), (9.0, 10.0),
        rv.RelevantWiring("kids", "subtract", "Children who leave before the stickers are handed out are no longer among the "
                                              "children who share them, so the number of sharers is reduced."),
        (Pair("p0", "Before the stickers were handed out, {value} {unit} went home {relation}.", "from her class",
              "from the class next door", CO_PRESENT,
              "Children of the class next door are not among the children this teacher shares with, so their leaving changes "
              "nobody in her group.", ("shares the rest equally among 15 children",), "some children"),
         Pair("p1", "{value} {unit} {relation}.", "went home before the stickers were handed out", "were away on a trip last term", OTHER_EVENT,
              "The children were away on a trip last term and are back; their trip leaves them among the children who share the stickers.",
              ("shares the rest equally among 15 children",), "Some children"))))

# --- NP07 a changed order (replace) -------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP07", "Cost of a lunch order", "restaurant bill",
        "Omar orders a soup for {soup} dollars and {salads} salads at {salad} dollars each. He leaves a {tip} dollar tip and uses "
        "a coupon worth {coupon} dollars. Dina sits at the next table.",
        "How many dollars does he pay in all?", "dollars he pays in all", "total", "dollars",
        (I("soup", "price of the soup", 6, "dollars"), I("salads", "number of salads", 2, "salads"),
         I("salad", "price of one salad", 8, "dollars"), I("tip", "tip", 3, "dollars"), I("coupon", "value of the coupon", 4, "dollars")),
        (N("salad_cost", "salads*salad", "cost of the salads", "dollars", EQUAL_GROUPS, "The salads cost the same."),
         N("meal", "soup + salad_cost", "cost of the meal", "dollars", TOTAL, "The soup and the salads are paid together."),
         N("total", "meal + tip - coupon", "dollars he pays in all", "dollars", "Addition of the tip and subtraction of the coupon",
           "The tip is paid on top of the meal and the coupon takes its value off the bill.")),
        lambda soup, salads, salad, tip, coupon: tip + soup + salads * salad - coupon,
        "The solver adds the amounts and subtracts the coupon in one expression.",
        ("All prices are in dollars.", "The coupon is taken off what he pays."),
        "Find the cost of the meal, then add the tip and take the coupon off.",
        "He pays more than the cost of the meal minus the coupon and the total is not negative.",
        ("dollars does he pay in all", "pay in all", "dollars he pays in all"), ("total",)),
    npx.NPSpec(
        "NP07", "a dish", "dollars", (9.0, 18.0, 22.0), (11.0, 13.0),
        rv.RelevantWiring("soup", "replace", "The dish takes the soup's place in the order, so its price replaces the soup's "
                                             "price."),
        (Pair("p0", "The soup was changed for a dish that costs {value} {unit} {relation}.", "at Omar's table", "at Dina's table",
              CO_PRESENT,
              "Dina's table is a different order; the dish she gets is paid for in her own bill and does not change what Omar "
              "pays.", ("Omar orders a soup for 6 dollars",), "a few dollars"),
         Pair("p1", "A dish that costs {value} {unit} {relation}.", "replaced his soup", "was his order last year", OTHER_EVENT,
              "The dish was his order on a visit last year; nothing of that order remains in the order he is paying for now.",
              ("Omar orders a soup for 6 dollars",), "a few dollars"))))

# --- NP08 a scaled order (scale) ----------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP08", "Sandwiches left over", "catering and portions",
        "A caterer has an order for {platters} platters with {per} sandwiches on each platter. {eaten} sandwiches are eaten at the "
        "party and {taken} are taken home. Another party is held in the next hall.",
        "How many sandwiches are left over?", "number of sandwiches left over", "left", "sandwiches",
        (I("platters", "number of platters", 5, "platters"), I("per", "sandwiches on one platter", 16, "sandwiches"),
         I("eaten", "sandwiches eaten", 47, "sandwiches"), I("taken", "sandwiches taken home", 9, "sandwiches")),
        (N("made", "platters*per", "sandwiches on the platters", "sandwiches", EQUAL_GROUPS, "Every platter carries the same "
           "number of sandwiches."),
         N("gone", "eaten + taken", "sandwiches that went away", "sandwiches", TOTAL, "The eaten and the taken sandwiches are "
           "different sandwiches, so they add."),
         N("left", "made - gone", "sandwiches left over", "sandwiches", REMAINDER, "What is left over is what was on the platters "
           "minus what went away.")),
        lambda platters, per, eaten, taken: platters * per - eaten - taken,
        "The solver subtracts the eaten and the taken sandwiches from the sandwiches on the platters one after the other.",
        ("Every platter carries the same number of sandwiches.", "Sandwiches that are eaten or taken home are not counted again."),
        "Count the sandwiches on the platters, then take away those that were eaten or taken home.",
        "The number left over is a whole number and is smaller than the number on the platters.",
        ("sandwiches are left over", "left over", "number of sandwiches left over"), ("left",)),
    npx.NPSpec(
        "NP08", "a multiplier on the order", "times", (3.0, 4.0, 6.0), (2.0, 8.0),
        rv.RelevantWiring("platters", "scale", "Multiplying the order for this party multiplies the number of platters, and every "
                                               "platter still carries the same number of sandwiches."),
        (Pair("p0", "The number of platters was multiplied by {value} {relation}.", "for this party",
              "for the next hall's party", CO_PRESENT,
              "The party in the next hall has its own order and its own guests; its platters are not this party's platters.",
              ("has an order for 5 platters",), "a whole number"),
         Pair("p1", "The caterer multiplied the number of platters by {value} {relation}.", "for this party", "for last year's party", OTHER_EVENT,
              "The order for last year's party was filled and eaten a year ago; it leaves no platters among this party's order.",
              ("has an order for 5 platters",), "a whole number"))))

# --- NP09 school counts -------------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP09", "Students without a chair", "school and class counts",
        "A school has {classes} classes of {size} students each. The hall has {rows} rows with {seats} chairs in each row for the "
        "students. The teachers sit in the hall as well.",
        "How many students have no chair?", "number of students with no chair", "standing", "students",
        (I("classes", "number of classes", 9, "classes"), I("size", "students in one class", 28, "students"),
         I("rows", "number of rows of chairs", 6, "rows"), I("seats", "chairs in one row", 14, "chairs")),
        (N("students", "classes*size", "students in the school", "students", EQUAL_GROUPS, "Every class has the same number of "
           "students."),
         N("chairs", "rows*seats", "chairs for the students", "chairs", EQUAL_GROUPS, "Every row has the same number of chairs."),
         N("standing", "students - chairs", "students with no chair", "students", REMAINDER, "Each student takes one chair, so the "
           "students without a chair are those left after the chairs are used.")),
        lambda classes, size, rows, seats: size * classes - seats * rows,
        "The solver writes the two counts as products inside one subtraction.",
        ("Every class has the same number of students.", "Every row has the same number of chairs.",
         "Each student needs one chair."),
        "Count the students, count the chairs, and subtract.",
        "The number of students with no chair is not negative and is smaller than the number of students.",
        ("students have no chair", "no chair", "number of students with no chair"), ("standing",)),
    npx.NPSpec(
        "NP09", "rows of chairs", "rows", (3.0, 8.0, 10.0), (1.0, 5.0),
        rv.RelevantWiring("rows", "add", "Rows of chairs set up in the hall for the students add to the rows already there, and "
                                         "every row has the same number of chairs."),
        (Pair("p0", "{value} {unit} of chairs were also put out for {relation}.", "the students", "the teachers",
              CO_PRESENT,
              "Chairs set up for the teachers are not chairs for the students, so the students still have only the rows stated.",
              ("The hall has 6 rows with 14 chairs in each row for the students",), "Some rows"),
         Pair("p1", "{value} {unit} of chairs were also set up in the hall {relation}.", "for the students", "for last year's concert", OTHER_EVENT,
              "Chairs set up for last year's concert were stacked away long ago, so the students have only the rows stated.",
              ("The hall has 6 rows with 14 chairs in each row for the students",), "Some rows"))))

# --- NP10 work schedules ------------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP10", "Rooms still to clean", "work schedule in tasks",
        "A hotel has {rooms} rooms to clean this week. {cleaners} cleaners each clean {per} rooms a day for {days} days. Another hotel stands next door.",
        "How many rooms are still to be cleaned at the end of the week?", "number of rooms still to be cleaned", "left", "rooms",
        (I("rooms", "rooms to clean this week", 600, "rooms"), I("cleaners", "number of cleaners", 4, "cleaners"),
         I("per", "rooms one cleaner cleans in a day", 6, "rooms"), I("days", "days of cleaning", 5, "days")),
        (N("daily", "cleaners*per", "rooms cleaned in a day", "rooms", EQUAL_GROUPS, "Every cleaner cleans the same number of "
           "rooms."),
         N("cleaned", "daily*days", "rooms cleaned in the week", "rooms", EQUAL_GROUPS, "The same number of rooms is cleaned on "
           "each day."),
         N("left", "rooms - cleaned", "rooms still to clean", "rooms", REMAINDER, "What is still to clean is what had to be cleaned "
           "minus what was cleaned.")),
        lambda rooms, cleaners, per, days: rooms - days * per * cleaners,
        "The solver multiplies the three working factors in one product before subtracting.",
        ("Every cleaner cleans the same number of rooms each day.", "No room is cleaned twice."),
        "Find how many rooms are cleaned in the week, then subtract from the rooms to clean.",
        "The number of rooms left is not negative and is smaller than the number to clean.",
        ("rooms are still to be cleaned", "still to be cleaned", "number of rooms still to be cleaned"), ("left",)),
    npx.NPSpec(
        "NP10", "more cleaners", "cleaners", (2.0, 9.0, 11.0), (3.0, 10.0),
        rv.RelevantWiring("cleaners", "add", "Cleaners who work in this hotel add to the cleaners already working, and each one "
                                             "cleans the same number of rooms a day."),
        (Pair("p0", "{value} {unit} from an agency also worked {relation} all week.", "in this hotel", "in the hotel next door", CO_PRESENT,
              "Cleaners in the hotel next door clean that hotel's rooms; none of this hotel's rooms is cleaned by them.",
              ("4 cleaners each clean 6 rooms a day for 5 days",), "Some cleaners"),
         Pair("p1", "{value} {unit} on the hotel's own staff also worked here {relation}.", "this week", "last summer", OTHER_EVENT,
              "Cleaners who worked here last summer cleaned rooms of last summer; they clean none of this week's rooms.",
              ("4 cleaners each clean 6 rooms a day for 5 days",), "Some cleaners"))))

# --- NP11 sports scores (replace) ---------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP11", "Points still needed to qualify", "sports scores",
        "A league gives {win} points for a win and {draw} point for a draw. After Friday, the Owls have {wins} wins and {draws} "
        "draws and need {goal} points to qualify. The Falcons play in a cup that has its own committee.",
        "How many more points do they need?", "number of more points they need", "needed", "points",
        (I("win", "points for a win", 3, "points"), I("draw", "points for a draw", 1, "points"),
         I("wins", "number of wins", 7, "games"), I("draws", "number of draws", 4, "games"),
         I("goal", "points needed to qualify", 40, "points")),
        (N("from_wins", "wins*win", "points from wins", "points", EQUAL_GROUPS, "Every win gives the same number of points."),
         N("from_draws", "draws*draw", "points from draws", "points", EQUAL_GROUPS, "Every draw gives the same number of points."),
         N("needed", "goal - from_wins - from_draws", "more points needed", "points", REMAINDER, "What is still needed is the "
           "qualifying mark minus the points already won.")),
        lambda win, draw, wins, draws, goal: goal - (win * wins + draw * draws),
        "The solver sums the points of wins and draws in one expression inside the subtraction.",
        ("Only wins and draws give points.", "The qualifying mark is the number of points they must reach."),
        "Count the points won so far, then find how far that is from the qualifying mark.",
        "They have not qualified yet, so the number of points still needed is positive.",
        ("more points do they need", "points they need", "number of more points they need"), ("needed",)),
    npx.NPSpec(
        "NP11", "a new qualifying mark", "points", (33.0, 35.0, 38.0), (45.0, 47.0),
        rv.RelevantWiring("goal", "replace", "A changed qualifying mark replaces the mark of 40 points, so the points still needed "
                                             "are measured from the new mark."),
        (Pair("p0", "{relation} changed the qualifying mark to {value} {unit}.", "The league", "The cup committee", CO_PRESENT,
              "The cup committee's mark belongs to a different competition; the Owls' mark in the league stays the stated one.",
              ("need 40 points to qualify",), "a new number of points"),
         Pair("p1", "The league changed the qualifying mark to {value} {unit} {relation}.", "for this season", "for last season", OTHER_EVENT,
              "A mark set for last season does not stand now; the mark for this season is the stated one.",
              ("need 40 points to qualify",), "a new number of points"))))

# --- NP12 library books -------------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP12", "Books on the shelves", "library books",
        "A library has {shelves} shelves with {per} books on each shelf. {loaned} books are out on loan and {repair} are being "
        "repaired. The school library next door also lends books.",
        "How many books are on the shelves?", "number of books on the shelves", "on_shelf", "books",
        (I("shelves", "number of shelves", 8, "shelves"), I("per", "books on one shelf", 35, "books"),
         I("loaned", "books out on loan", 94, "books"), I("repair", "books being repaired", 11, "books")),
        (N("total", "shelves*per", "books the library owns", "books", EQUAL_GROUPS, "Every shelf holds the same number of books."),
         N("away", "loaned + repair", "books that are not on the shelves", "books", TOTAL, "The loaned and the repaired books are "
           "different books, so they add."),
         N("on_shelf", "total - away", "books on the shelves", "books", REMAINDER, "The books on the shelves are those that are "
           "not away.")),
        lambda shelves, per, loaned, repair: per * shelves - repair - loaned,
        "The solver subtracts the repaired and the loaned books from the library's books one after the other.",
        ("Every shelf holds the same number of books.", "A book is either on a shelf, on loan or being repaired."),
        "Count the books the library has, count those that are away, and subtract.",
        "The number on the shelves is not negative and is smaller than the number the library owns.",
        ("books are on the shelves", "on the shelves", "number of books on the shelves"), ("on_shelf",)),
    npx.NPSpec(
        "NP12", "books returned", "books", (7.0, 21.0, 26.0), (32.0, 33.0),
        rv.RelevantWiring("loaned", "subtract", "Books returned to this library are no longer on loan, so the number out on "
                                               "loan is reduced."),
        (Pair("p0", "{value} {unit} were returned {relation} on Friday.", "to this library", "to the school library", CO_PRESENT,
              "Books returned to the school library belong to that library; none of this library's loans ends.",
              ("94 books are out on loan",), "Some books"),
         Pair("p1", "{value} {unit} were returned to this library {relation}.", "this week", "last year", OTHER_EVENT,
              "Books returned last year ended loans of last year; the loans now out are the stated ones.",
              ("94 books are out on loan",), "Some books"))))

# --- NP13 garden rows ---------------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP13", "Seedlings left in a garden", "garden rows",
        "A gardener plants {rows} rows with {per} seedlings in each row. Snails eat {eaten} seedlings, and she gives {gift} "
        "seedlings to a neighbour. A plot next door belongs to the neighbour.",
        "How many seedlings are left in her garden?", "number of seedlings left in her garden", "left", "seedlings",
        (I("rows", "number of rows", 6, "rows"), I("per", "seedlings in one row", 14, "seedlings"),
         I("eaten", "seedlings eaten by snails", 17, "seedlings"), I("gift", "seedlings given away", 9, "seedlings")),
        (N("planted", "rows*per", "seedlings planted", "seedlings", EQUAL_GROUPS, "Every row has the same number of seedlings."),
         N("gone", "eaten + gift", "seedlings that are gone", "seedlings", TOTAL, "The eaten and the given seedlings are different "
           "seedlings, so they add."),
         N("left", "planted - gone", "seedlings left in the garden", "seedlings", REMAINDER, "What is left is what was planted "
           "minus what is gone.")),
        lambda rows, per, eaten, gift: per * rows - gift - eaten,
        "The solver subtracts the given and the eaten seedlings from the planted ones one after the other.",
        ("Every row has the same number of seedlings.", "A seedling that is eaten or given away is not counted again."),
        "Count the seedlings planted, count those that are gone, and subtract.",
        "The number left is not negative and is smaller than the number planted.",
        ("seedlings are left in her garden", "left in her garden", "number of seedlings left in her garden"), ("left",)),
    npx.NPSpec(
        "NP13", "seedlings in every row", "seedlings", (7.0, 8.0, 11.0), (3.0, 4.0),
        rv.RelevantWiring("per", "add", "Seedlings planted in every row of her garden add to the seedlings already in each row, so "
                                        "every one of the rows holds more."),
        (Pair("p0", "{value} {unit} were also planted in every row {relation}.", "of her garden", "of the plot next door",
              CO_PRESENT, "Seedlings planted in the plot next door grow in that plot; none of them is in her garden.",
              ("plants 6 rows with 14 seedlings in each row",), "Some seedlings"),
         Pair("p1", "{value} {unit} were also planted in every row of her garden {relation}.", "this year", "last year", OTHER_EVENT,
              "Seedlings planted last year grew, were picked or died long ago; they are no part of the rows now planted.",
              ("plants 6 rows with 14 seedlings in each row",), "Some seedlings"))))

# --- NP14 a school timetable (replace) ----------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP14", "Length of a school day", "school timetable",
        "A school day has {periods} lessons of {lesson} minutes each and {breaks} breaks of {blen} minutes each. Another school stands across the road.",
        "How many minutes long is the school day?", "number of minutes in the school day", "day", "minutes",
        (I("periods", "number of lessons", 6, "lessons"), I("lesson", "minutes in one lesson", 45, "minutes"),
         I("breaks", "number of breaks", 3, "breaks"), I("blen", "minutes in one break", 15, "minutes")),
        (N("lesson_total", "periods*lesson", "minutes of lessons", "minutes", EQUAL_GROUPS, "Every lesson lasts the same number of "
           "minutes."),
         N("break_total", "breaks*blen", "minutes of breaks", "minutes", EQUAL_GROUPS, "Every break lasts the same number of "
           "minutes."),
         N("day", "lesson_total + break_total", "minutes in the school day", "minutes", TOTAL, "The lessons and the breaks follow "
           "each other, so their minutes add.")),
        lambda periods, lesson, breaks, blen: periods * lesson + blen * breaks,
        "The solver adds the two products in one expression.",
        ("Lessons and breaks follow each other without gaps.", "Every lesson lasts the same number of minutes."),
        "Count the minutes of the lessons, count the minutes of the breaks, and add.",
        "The day is longer than its lessons alone.",
        ("minutes long is the school day", "school day", "number of minutes in the school day"), ("day",)),
    npx.NPSpec(
        "NP14", "minutes in a lesson", "minutes", (20.0, 34.0, 38.0), (32.0, 42.0),
        rv.RelevantWiring("lesson", "replace", "A changed lesson length replaces the stated length of a lesson, so every lesson lasts "
                                            "the new number of minutes."),
        (Pair("p0", "Every lesson was changed to {value} {unit} {relation}.", "at this school", "at the school across the road",
              CO_PRESENT, "A lesson at the school across the road is a lesson of another school's day, not of this school's day.",
              ("A school day has 6 lessons of 45 minutes each",), "a new number of minutes"),
         Pair("p1", "Every lesson was changed to {value} {unit} for {relation}.", "this term", "last term", OTHER_EVENT,
              "A length set for last term does not stand now; this term's lessons are the stated length.",
              ("A school day has 6 lessons of 45 minutes each",), "a new number of minutes"))))

# --- NP15 buses (replace, division) ---------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP15", "Buses for a school trip", "seating and division",
        "A school trip has {students} students and {teachers} teachers. Each bus seats {seats} people. The band group travels from the same school.",
        "How many buses does the trip need?", "number of buses the trip needs", "buses", "buses",
        (I("students", "number of students", 165, "students"), I("teachers", "number of teachers", 15, "teachers"),
         I("seats", "people one bus seats", 20, "seats")),
        (N("people", "students + teachers", "people on the trip", "people", TOTAL, "The students and the teachers are different "
           "people, so they add."),
         N("buses", "people/seats", "buses needed", "buses", SHARE, "The people are split into equal bus loads.")),
        lambda students, teachers, seats: (teachers + students) / seats,
        "The solver adds the teachers to the students inside one quotient.",
        ("Every bus is filled to its seats.", "Every person needs one seat."),
        "Count the people on the trip, then divide by the seats of one bus.",
        "The buses are full, so the number of buses is a whole number.",
        ("buses does the trip need", "trip need", "number of buses the trip needs"), ("buses",)),
    npx.NPSpec(
        "NP15", "seats in a bus", "seats", (12.0, 18.0, 45.0), (30.0, 36.0),
        rv.RelevantWiring("seats", "replace", "Buses with a different number of seats replace the buses of 20 seats, so "
                                              "the people are divided by the new number of seats."),
        (Pair("p0", "{relation} switched to buses with {value} {unit} each.", "The school group", "The band group", CO_PRESENT,
              "The band group travels on its own buses; the school group's buses are still the stated ones.",
              ("Each bus seats 20 people",), "a different number of seats"),
         Pair("p1", "The school group switched to buses with {value} {unit} each {relation}.", "for this trip", "for last year's trip", OTHER_EVENT,
              "Buses hired for last year's trip are not the buses of this trip, which seat the stated number.",
              ("Each bus seats 20 people",), "a different number of seats"))))

# --- NP16 print jobs (scale) --------------------------------------------------------------------------------------------------

_add(
    npx.NPStructure(
        "NP16", "Sheets of paper to load", "print jobs",
        "A teacher prints {copies} copies of a worksheet for each of {classes} classes. Each worksheet uses {pages} sheets of "
        "paper, and the tray already holds {have} sheets. The art teacher uses the same printer.",
        "How many more sheets of paper does she need to load?", "number of sheets she needs to load", "needed", "sheets",
        (I("copies", "copies for each class", 28, "copies"), I("classes", "number of classes", 3, "classes"),
         I("pages", "sheets of paper in one worksheet", 2, "sheets"), I("have", "sheets already in the tray", 75, "sheets")),
        (N("worksheets", "classes*copies", "worksheets printed", "worksheets", EQUAL_GROUPS, "Every class gets the same number of "
           "copies."),
         N("sheets", "worksheets*pages", "sheets of paper used", "sheets", EQUAL_GROUPS, "Every worksheet uses the same number of "
           "sheets."),
         N("needed", "sheets - have", "sheets still to load", "sheets", REMAINDER, "What she must load is what the printing uses "
           "minus what the tray holds.")),
        lambda copies, classes, pages, have: pages * copies * classes - have,
        "The solver multiplies the three factors in one product before subtracting.",
        ("Every class gets the same number of copies.", "Every worksheet uses the same number of sheets."),
        "Count the sheets the printing uses, then subtract the sheets already in the tray.",
        "She needs to load some paper, so the answer is positive and less than the sheets used.",
        ("sheets of paper does she need", "need to load", "number of sheets she needs to load"), ("needed",)),
    npx.NPSpec(
        "NP16", "a multiplier on the copies", "times", (9.0, 10.0, 12.0), (4.0, 7.0),
        rv.RelevantWiring("copies", "scale", "Multiplying the copies per class multiplies the worksheets printed, and every "
                                             "worksheet uses the same number of sheets."),
        (Pair("p0", "The number of copies per class was multiplied by {value} in {relation}.", "her print order",
              "the art teacher's print order", CO_PRESENT,
              "The art teacher's print order is a different job; the sheets it uses are not sheets of this print job.",
              ("prints 28 copies of a worksheet for each of 3 classes",), "a whole number"),
         Pair("p1", "The number of copies per class was multiplied by {value} {relation}.", "for this worksheet", "for last term's worksheet", OTHER_EVENT,
              "The multiplier for last term's worksheet belongs to a job printed last term; this worksheet's order is the stated one.",
              ("prints 28 copies of a worksheet for each of 3 classes",), "a whole number"))))
