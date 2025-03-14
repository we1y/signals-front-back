'use client'

import { Button } from "@/components/ui/common/button";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { reinvestService } from "@/services/reinvest.service";


export default function Reinvest() {
    const t = useTranslations("Plans");
    const router = useRouter();
    const [selectedValue, setSelectedValue] = useState<number>(25);
    const queryClient = useQueryClient();

    const values = [
      {
        id: 1, 
        value: 25
      },
      {
        id: 2, 
        value: 50
      },
      {
        id: 3, 
        value: 75
      },
      {
        id: 4, 
        value: 100
      },
    ]

    const handleValueClick = (value: number) => {
        setSelectedValue(value);
    };

    const reinvest = useMutation({
      mutationKey: ['update reinvest'],
      mutationFn: (value: number) => reinvestService.setUserReinvest(value),
      onError: (error: any) => console.log(error),
      onSuccess: () => {
        queryClient.invalidateQueries();
        router.push(`/success?message=${encodeURIComponent("Процент для реинвестирования успешно изменен")}`);
      }
    });

    return (
        <div className='space-y-4 m-4'>
            <h1 className="text-black flex justify-center font-bold">{t("reinvest")}</h1>
            <h2 className="text-black flex justify-center font-bold text-center">{t("reinvestprofit")}</h2>
            <div className="grid grid-rows-2 grid-cols-2 gap-2">
                {values.map((value) => (
                 <div key={value.id} className={`${selectedValue == value.value ? "bg-primary" : "bg-muted"} p-2 text-center rounded-full cursor-pointer`} onClick={() => handleValueClick(value.value)}>{value.value}%</div>
                ))}
            </div>
            <p className="text-muted text-center">Нажимая кнопку "Принять", вы соглашаетесь с выбранными условиями и отменить их будет невозможно!</p>
            <Button className="bg-primary hover:bg-primary text-primary-foreground w-full" onClick={() => reinvest.mutate(selectedValue)}>{t("accept")}</Button>
        </div>
    )
}