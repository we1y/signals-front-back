'use client'

import { Card } from "@/components/ui/common/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/common/tabs";
import { Button } from "@/components/ui/common/button";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { planService } from "@/services/plan.service";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { reinvestService } from "@/services/reinvest.service";
import Image from "next/image";
import premium from '../../../../public/icons/yellow.png';
import standart from '../../../../public/icons/blue.png';
import premiumplus from '../../../../public/icons/green.png';

export default function Plans() {
    const t = useTranslations("Plans");
    const router = useRouter();
    const [plan, setPlan] = useState<number>(0);
    const [content, setContent] = useState<string>("plan");
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

    const { data } = useQuery({
      queryKey: ['user plan'],
      queryFn: () => planService.getUserPlan()
    });

    const plans = useMutation({
      mutationKey: ['update plan'],
      mutationFn: (plan_id: number) => planService.updateUserPlan(plan_id),
      onError: (error: any) => console.log(error),
      onSuccess: () => {
        queryClient.invalidateQueries();
      }
    });

    const reinvest = useMutation({
      mutationKey: ['update reinvest'],
      mutationFn: (value: number) => reinvestService.setUserReinvest(value),
      onError: (error: any) => console.log(error),
      onSuccess: () => {
        queryClient.invalidateQueries();
      }
    });

    const handleTabChange = (value: any) => {
        setPlan(parseInt(value));
    };

    const accept = () => {
      plans.mutate(plan);
      reinvest.mutate(selectedValue)
      router.push('/')
    }

    return (
        <div className='space-y-4 m-4'>
          {content === "plan" ? (
            <>
              <div className="flex flex-row space-x-2 justify-center">
                <div className="bg-primary w-10 h-2 rounded-full"></div>
                <div className="bg-muted w-10 h-2 rounded-full"></div>
              </div>
              <Card className="p-2 font-bold flex justify-center">
                  {t("currentplan")}: {data === 0 ? t("standart") : 
                  data === 1 ? t("premium") : 
                  data === 2 ? t("premiumplus") : 
                  'Unknown'}
              </Card>
              <h1 className="text-black flex justify-center font-bold">{t("work")}</h1>
              <Tabs defaultValue="0" onValueChange={handleTabChange}>
                <TabsList className="grid w-full h-full grid-cols-3 bg-foreground space-x-2">
                  <TabsTrigger value="0" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={standart} alt="" width={60} height={60}/>
                    {t("standart")}
                  </TabsTrigger>
                  <TabsTrigger value="1" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={premium} alt="" width={60} height={60}/>
                    {t("premium")}
                  </TabsTrigger>
                  <TabsTrigger value="2" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={premiumplus} alt="" width={60} height={60}/>
                    {t("premiumplus")}
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="0">
                    <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">2</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">2</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
                <TabsContent value="1">
                  <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">4</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">4</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
                <TabsContent value="2">
                    <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">5</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">5</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
              </Tabs>
              <div className="flex justify-between space-x-2">
                <Button className="bg-primary text-primary-foreground hover:bg-primary w-full" onClick={() => setContent("reinvest")}>{t("next")}</Button>
              </div>
            </>
          ) : (
            <>
              <div className="flex flex-row space-x-2 justify-center">
                <div className="bg-muted w-10 h-2 rounded-full"></div>
                <div className="bg-primary w-10 h-2 rounded-full"></div>
              </div>
              <h1 className="text-black flex justify-center font-bold">{t("reinvest")}</h1>
              <h2 className="text-black flex justify-center font-bold text-center">{t("reinvestprofit")}</h2>
              <div className="grid grid-rows-2 grid-cols-2 gap-2">
                  {values.map((value) => (
                    <div key={value.id} className={`${selectedValue == value.value ? "bg-primary" : "bg-muted"} p-2 text-center rounded-full cursor-pointer`} onClick={() => handleValueClick(value.value)}>{value.value}%</div>
                  ))}
              </div>
              <p className="text-muted text-center">Нажимая кнопку "Принять", вы соглашаетесь с выбранными условиями и отменить их будет невозможно!</p>
              <div className="flex flex-row space-x-2">
                <Button className="bg-muted hover:bg-muted text-primary-foreground w-full" onClick={() => setContent("plan")}>{t("back")}</Button>
                <Button className="bg-primary hover:bg-primary text-primary-foreground w-full" onClick={accept}>{t("accept")}</Button>
              </div>
            </>
          )}
        </div>
    )
}