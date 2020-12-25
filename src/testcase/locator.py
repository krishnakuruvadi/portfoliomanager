from selenium.webdriver.common.by import By

class FDAddPageLocator(object):
    NUMBER_INPUT = (By.ID, "number")
    BANK_NAME_INPUT = (By.ID, "bank_name")
    START_DATE_INPUT = (By.ID, "start_date")
    USER_INPUT = (By.ID, "id_user")
    GOAL_INPUT = (By.ID, "id_goal")
    PRINCIPAL_INPUT = (By.ID, "principal")
    ROI_INPUT = (By.ID, "roi")
    TIME_PERIOD_INPUT = (By.ID, "time_period_days")
    MATURITY_DATE_INPUT = (By.ID, "mat_date")
    NOTES_INPUT = (By.NAME, "notes")

    CALCULATE_BUTTON = (By.NAME, "calculate")
    SUBMIT_BUTTON = (By.NAME, "submit")
    CANCEL_BUTTON = (By.NAME, "cancel")

class FDListPageLocator(object):
    FD_TABLE = (By.ID, "fixed_deposits")