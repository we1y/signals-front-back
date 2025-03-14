'use client'

import BackButton from "@/components/features/telegram/BackButton";
import { Card, CardHeader } from "@/components/ui/common/card";



export default function Notifications() {
    return (
        <>
            <BackButton />
            <Card className='shadow-none text-center m-2 p-4'>
                <CardHeader className="space-y-8">
                    
                </CardHeader>
            </Card>
        </>
    );
}