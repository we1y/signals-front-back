export interface CustomSignal {
    name: string
	join_time: number
    active_time: number
    burn_chance: number
    profit_percent: number
}

export type RandomSignal = {
    name: string
}

export type ActiveSignals = {
    active_signals: ActiveSignal[]
}

interface ActiveSignal {
    signal_id: number
    name: string
    join_until: Date
    expires_at: Date
    signal_cost: number
    burn_chance: number
    profit_percent: number
}

export interface JoinSignal {
    telegram_id: number,
    signal_id: number
}

export interface JoinSignalResponse {
    message: string;
    success: boolean;
    required_amount?: number;
    current_balance?: number;
}

export interface Profits {
    id: number,
    amount: number
    signal_id: number
    created_at: Date
}