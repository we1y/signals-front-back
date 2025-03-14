export interface User {
    id: number
    telegram_id: number
    username: string
    first_name: string
    last_name: string
    language_code: string
    photo_url: string
    created_at: Date
    updated_at: Date
    is_bot: boolean
    automod: boolean
    plan: number
    in_work: number
}

export interface EnableAutomodResponse {
    message: string
    success: boolean
    required_amount: number
    current_balance: number
}

export interface DisableAutomodResponse {
    message: string
    success: boolean
}